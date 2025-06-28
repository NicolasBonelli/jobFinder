import os
import json
import boto3
from datetime import datetime
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
PROFILES_PREFIX = "users/"
RESULTS_PREFIX = "matchedJobs/"
JOBS_KEY = "jobs/latest.json"

s3 = boto3.client("s3")
model = SentenceTransformer("intfloat/e5-base-v2")


def expand_user_skills(skills):
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
    user_skills_set = set(s.lower() for s in user_skills)
    job_skills_set = set(s.lower() for s in job_skills)
    intersection = user_skills_set & job_skills_set
    return len(intersection) / max(1, len(user_skills_set)), list(intersection)


def calculate_match_score(user_profile, job):
    user_skills = expand_user_skills(user_profile.get("skills", []))
    job_skills = job.get("requirements", [])

    if not job_skills:
        return 0.0, []

    user_text = "query: " + ", ".join(user_skills)
    job_text = "passage: " + ", ".join(job_skills)

    user_embedding = model.encode(user_text)
    job_embedding = model.encode(job_text)

    cos_sim = cosine_similarity([user_embedding], [job_embedding])[0][0]
    overlap_score, matched_skills = keyword_overlap(user_skills, job_skills)
    final_score = float(round(0.7 * cos_sim + 0.3 * overlap_score, 4))

    return final_score, matched_skills


def get_user_profiles():
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=PROFILES_PREFIX)
    if 'Contents' not in response:
        return []

    profiles = []
    for obj in response['Contents']:
        key = obj['Key']
        if key.endswith('.json') and key != PROFILES_PREFIX:
            file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=key)
            content = file_obj['Body'].read().decode('utf-8')
            data = json.loads(content)
            data['user_id'] = Path(key).stem
            profiles.append(data)
            print(f"✅ Perfil cargado: {key}")
    return profiles


def get_jobs():
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=JOBS_KEY)
        jobs_json = json.loads(response['Body'].read().decode('utf-8'))
        print(f"📋 {len(jobs_json)} trabajos disponibles")
        return jobs_json
    except Exception as e:
        print(f"❌ Error leyendo trabajos: {e}")
        return []


def save_match_result_to_s3(user_id, result_data):
    try:
        key = f"{RESULTS_PREFIX}{user_id}.json"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=json.dumps(result_data, ensure_ascii=False, indent=2).encode('utf-8'),
            ContentType="application/json"
        )
        print(f"✅ Match guardado: {key}")
    except Exception as e:
        print(f"❌ Error subiendo {user_id}.json: {e}")


def main():
    print("🚀 Iniciando matcher...")
    print(f"⏰ Timestamp: {datetime.now().isoformat()}")

    user_profiles = get_user_profiles()
    if not user_profiles:
        print("⚠️ No se encontraron usuarios")
        return

    jobs = get_jobs()
    if not jobs:
        print("⚠️ No se encontraron trabajos")
        return

    total_matches = 0
    for user in user_profiles:
        user_id = user["user_id"]
        print(f"\n🔍 Matcheando para usuario {user_id}")
        matched = []
        for job in jobs:
            score, matched_skills = calculate_match_score(user, job)
            if score >= 0.7:
                matched.append({
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
        matched.sort(key=lambda x: x["score"], reverse=True)

        # Ordenar por score descendente y quedarnos con los top 4
        top_matches = sorted(matched, key=lambda x: x["score"], reverse=True)[:4]

        # Guardar directamente como array de trabajos
        save_match_result_to_s3(user_id, top_matches)
        total_matches += len(matched)

    print(f"\n🎉 Match finalizado. Usuarios: {len(user_profiles)}, Matches totales: {total_matches}")


if __name__ == "__main__":
    main()
