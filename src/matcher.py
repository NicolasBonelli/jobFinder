import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# 🔹 Modelo optimizado para búsqueda semántica
model = SentenceTransformer("intfloat/e5-base-v2")

# 🔹 Expandir perfil de usuario
def expand_user_skills(skills):
    expansions = {
        "Python": ["backend", "APIs", "ORM"],
        "FastAPI": ["REST", "web development"],
        "SQL": ["databases", "PostgreSQL", "MySQL"],
        "AWS": ["cloud", "infrastructure"],
        "React": ["frontend", "UI"],
        "Docker": ["containers", "DevOps"],
        "Remote": ["teletrabajo", "distributed"],
    }
    expanded = set(skills)
    for skill in skills:
        expanded.update(expansions.get(skill, []))
    return list(expanded)

# 🔹 Overlap entre skills
def keyword_overlap(user_skills, job_skills):
    user_skills_set = set(s.lower() for s in user_skills)
    job_skills_set = set(s.lower() for s in job_skills)
    return len(user_skills_set & job_skills_set) / max(1, len(user_skills_set))

# 📥 Cargar perfil del usuario
with open("user_profile.json", "r", encoding="utf-8") as f:
    user_profile = json.load(f)

user_skills = expand_user_skills(user_profile["skills"])
user_text = "query: " + ", ".join(user_skills)
user_embedding = model.encode(user_text)

# 📥 Cargar todas las ofertas
offers = []
for json_file in Path("output").glob("*.json"):
    with open(json_file, "r", encoding="utf-8") as f:
        offers += json.load(f)

# 🔎 Procesar y matchear
matched_jobs = []

for job in offers:
    job_skills = job.get("requirements", [])
    if not job_skills:
        continue

    job_text = "passage: " + ", ".join(job_skills)
    job_embedding = model.encode(job_text)

    cos_sim = cosine_similarity([user_embedding], [job_embedding])[0][0]
    overlap_score = keyword_overlap(user_skills, job_skills)

    final_score = float(round(0.7 * cos_sim + 0.3 * overlap_score, 4))


    if final_score >= 0.75:
        matched_jobs.append({
            "title": job["title"],
            "company": job["company"],
            "url": job["url"],
            "score": final_score,
            "skills_match": list(set(user_skills) & set(job_skills)),
            "description": job["description"],
            "requirements": job_skills,
            "location": job.get("location", "N/A"),
            "job_type": job.get("job_type", "N/A"),
            "date_posted": job.get("date_posted", "N/A"),
            "salary": job.get("salary", "Not specified")
        })

# 💾 Guardar resultados
with open("matched_jobs.json", "w", encoding="utf-8") as f:
    json.dump(matched_jobs, f, indent=2, ensure_ascii=False)

print(f"✅ Se encontraron {len(matched_jobs)} ofertas compatibles con el perfil.")
