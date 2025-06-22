import uuid
import json
from bs4 import BeautifulSoup
from config import OUTPUT_DIR

async def extract_job_links(html):
    """Extrae los enlaces de las ofertas de empleo desde el HTML."""
    soup = BeautifulSoup(html, "html.parser")
    job_links = []
    for a_tag in soup.find_all("a", class_="gb-results-list__item"):
        href = a_tag.get("href")
        if href and "/jobs/" in href:
            full_url = f"https://www.getonboard.com{href}" if href.startswith("/") else href
            job_links.append(full_url)
    return job_links

async def extract_job_details(crawler, url, chain):
    """Extrae el texto de una oferta de empleo con BeautifulSoup y lo procesa con un LLM."""
    from config import RUN_CONFIG  # Importar aquí para evitar circularidad
    
    result = await crawler.arun(url, config=RUN_CONFIG)
    
    if not result.success:
        print(f"❌ Falló el scraping de {url}: {result.error_message}")
        return None

    # Guardar el HTML para depuración
    job_id = str(uuid.uuid4())
    html_file = OUTPUT_DIR / f"debug_job_{job_id}.html"
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(result.html)

    # Extraer texto con BeautifulSoup
    with open(html_file, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    # Guardar el texto para depuración
    text_file = OUTPUT_DIR / f"debug_job_{job_id}.txt"
    with open(text_file, "w", encoding="utf-8") as f:
        f.write(text)

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
        print(f"Contenido del archivo de texto: {text_file}")
        return None
    except Exception as e:
        print(f"❌ Error al procesar con LLM {url}: {e}")
        return None