import json
import boto3
from pathlib import Path
from datetime import datetime
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from config import BUCKET_NAME, PROFILES_PREFIX, RESULTS_PREFIX, LOCAL_PROFILES_DIR, LOCAL_RESULTS_DIR

# Inicializar S3 y modelo
s3 = boto3.client('s3')
model = SentenceTransformer("intfloat/e5-base-v2")

def expand_user_skills(skills):
    """Expandir perfil de usuario con sinónimos"""
    expansions = {
        "Python": ["backend", "APIs", "ORM", "Django", "Flask"],
        "FastAPI": ["REST", "web development", "API"],
        "SQL": ["databases", "PostgreSQL", "MySQL", "queries"],
        "AWS": ["cloud", "infrastructure", "S3", "Lambda"],
        "React": ["frontend", "UI", "JavaScript", "JSX"],
        "Docker": ["containers", "DevOps", "deployment"],
        "Remote": ["teletrabajo", "distributed", "work from home"],
        "JavaScript": ["JS", "frontend", "backend", "Node.js"],
        "Git": ["version control", "GitHub", "GitLab"],
    }
    expanded = set(skills)
    for skill in skills:
        expanded.update(expansions.get(skill, []))
    return list(expanded)

def keyword_overlap(user_skills, job_skills):
    """Calcular overlap entre skills del usuario y trabajo"""
    user_skills_set = set(s.lower() for s in user_skills)
    job_skills_set = set(s.lower() for s in job_skills)
    intersection = user_skills_set & job_skills_set
    return len(intersection) / max(1, len(user_skills_set)), list(intersection)

def calculate_match_score(user_profile, job):
    """Calcular score de match entre usuario y trabajo"""
    user_skills = expand_user_skills(user_profile.get("skills", []))
    job_skills = job.get("requirements", [])
    
    if not job_skills:
        return 0.0, []
    
    # Embeddings semánticos
    user_text = "query: " + ", ".join(user_skills)
    job_text = "passage: " + ", ".join(job_skills)
    
    user_embedding = model.encode(user_text)
    job_embedding = model.encode(job_text)
    
    cos_sim = cosine_similarity([user_embedding], [job_embedding])[0][0]
    overlap_score, matched_skills = keyword_overlap(user_skills, job_skills)
    
    # Score final combinado
    final_score = float(round(0.7 * cos_sim + 0.3 * overlap_score, 4))
    
    return final_score, matched_skills

def download_profiles_from_s3():
    """Descargar todos los perfiles de usuario de S3"""
    print("📥 Descargando perfiles de usuario desde S3...")
    
    try:
        # Listar objetos en la carpeta profiles/
        response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PROFILES_PREFIX)
        
        if 'Contents' not in response:
            print("⚠️ No se encontraron perfiles en S3")
            return []
        
        profiles = []
        for obj in response['Contents']:
            key = obj['Key']
            if key.endswith('.json') and key != PROFILES_PREFIX:  # Evitar carpeta vacía
                # Descargar archivo
                local_path = LOCAL_PROFILES_DIR / Path(key).name
                s3.download_file(BUCKET_NAME, key, str(local_path))
                
                # Cargar JSON
                with open(local_path, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                    profile_data['user_id'] = Path(key).stem  # Extraer ID del nombre archivo
                    profiles.append(profile_data)
                
                print(f"✅ Descargado perfil: {Path(key).name}")
        
        print(f"📊 Total perfiles descargados: {len(profiles)}")
        return profiles
        
    except Exception as e:
        print(f"❌ Error descargando perfiles: {e}")
        return []

def process_user_matches(user_profile, all_jobs):
    """Procesar matches para un usuario específico"""
    user_id = user_profile.get('user_id', 'unknown')
    user_skills = user_profile.get('skills', [])
    
    print(f"🔍 Procesando matches para usuario {user_id} con skills: {user_skills}")
    
    matched_jobs = []
    for job in all_jobs:
        score, matched_skills = calculate_match_score(user_profile, job)
        
        # Solo incluir trabajos con score >= 0.75
        if score >= 0.75:
            matched_jobs.append({
                "title": job.get("title", "N/A"),
                "company": job.get("company", "N/A"),
                "url": job.get("url", "N/A"),
                "score": score,
                "skills_match": matched_skills,
                "description": job.get("description", "N/A"),
                "requirements": job.get("requirements", []),
                "location": job.get("location", "N/A"),
                "job_type": job.get("job_type", "N/A"),
                "date_posted": job.get("date_posted", "N/A"),
                "salary": job.get("salary", "Not specified")
            })
    
    # Ordenar por score descendente
    matched_jobs.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"✅ Usuario {user_id}: {len(matched_jobs)} trabajos encontrados")
    return matched_jobs

def upload_results_to_s3():
    """Subir todos los resultados a S3"""
    print("📤 Subiendo resultados a S3...")
    
    uploaded_count = 0
    for result_file in LOCAL_RESULTS_DIR.glob("*.json"):
        s3_key = f"{RESULTS_PREFIX}{result_file.name}"
        
        try:
            s3.upload_file(str(result_file), BUCKET_NAME, s3_key)
            print(f"✅ Subido: {s3_key}")
            uploaded_count += 1
        except Exception as e:
            print(f"❌ Error subiendo {result_file.name}: {e}")
    
    print(f"📊 Total archivos subidos: {uploaded_count}")
    return uploaded_count

def main():
    """Función principal del batch matcher"""
    print("🚀 Iniciando Batch Matcher...")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")
    
    # 1. Descargar perfiles de usuarios
    user_profiles = download_profiles_from_s3()
    if not user_profiles:
        print("❌ No hay perfiles para procesar")
        return
    
    # 2. Cargar trabajos scrapeados
    jobs_file = Path("scraped_jobs.json")
    if not jobs_file.exists():
        print("❌ No se encontró archivo de trabajos scrapeados")
        return
    
    with open(jobs_file, 'r', encoding='utf-8') as f:
        all_jobs = json.load(f)
    
    print(f"📋 Trabajos disponibles: {len(all_jobs)}")
    
    # 3. Procesar cada usuario
    total_matches = 0
    for user_profile in user_profiles:
        user_id = user_profile.get('user_id', 'unknown')
        matched_jobs = process_user_matches(user_profile, all_jobs)
        
        # Guardar resultados localmente
        result_file = LOCAL_RESULTS_DIR / f"{user_id}_matches.json"
        result_data = {
            "user_id": user_id,
            "processed_at": datetime.now().isoformat(),
            "total_matches": len(matched_jobs),
            "user_skills": user_profile.get('skills', []),
            "matches": matched_jobs
        }
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        total_matches += len(matched_jobs)
    
    # 4. Subir resultados a S3
    upload_results_to_s3()
    
    print(f"🎉 Batch Matcher completado!")
    print(f"👥 Usuarios procesados: {len(user_profiles)}")
    print(f"💼 Total matches encontrados: {total_matches}")

if __name__ == "__main__":
    main()