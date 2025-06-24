import uuid
import json
from bs4 import BeautifulSoup


async def extract_job_links(html):
    """Extrae los enlaces de las ofertas de empleo desde el HTML."""
    soup = BeautifulSoup(html, "html.parser")
    job_links = []
    for a_tag in soup.find_all("a", class_="gb-results-list__item"):
        href = a_tag.get("href")
        if href and "/jobs/" in href:
            full_url = f"https://www.getonboard.com{href}" if href.startswith("/") else href
            job_links.append(full_url)
    print(f"🔗 Enlaces extraídos: {len(job_links)}")
    if len(job_links) > 0:
        print(f"Primeros 3 enlaces: {job_links[:3]}")
    return job_links

async def extract_job_details(crawler, url, chain):
    """Extrae el texto de una oferta de empleo con BeautifulSoup y lo procesa con un LLM."""
    from config import RUN_CONFIG
    
    result = await crawler.arun(url, config=RUN_CONFIG)
    
    if not result.success:
        print(f"❌ Falló el scraping de {url}: {result.error_message}")
        return None


    job_id = str(uuid.uuid4())
    
    soup = BeautifulSoup(result.html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)


    try:
        # Procesar el texto con el LLM
        json_output = await chain.ainvoke({"job_text": text})
        # Imprimir la salida cruda para depuración
        print(f"Salida cruda del LLM para {url}:\n{json_output}\n")
        # Limpiar la salida para quitar markdown
        json_output = json_output.strip().strip("```json").strip("```").strip()
        # Parsear la salida como JSON
        job_details = json.loads(json_output)
        job_details["id"] = job_id
        job_details["url"] = url
        return job_details
    except json.JSONDecodeError as e:
        print(f"❌ Error al parsear JSON para {url}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error al procesar con LLM {url}: {e}")
        return None