import asyncio
import json
from pathlib import Path
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from bs4 import BeautifulSoup
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.schema.output_parser import StrOutputParser
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Verificar que la clave API esté configurada
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("GOOGLE_API_KEY no está definida en el archivo .env")

# Configuración de directorios
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

# URL inicial
URL = "https://www.getonbrd.com/jobs-remote"

# Inicializar el modelo LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.3)

# Prompt para el LLM
prompt_template = PromptTemplate(
    input_variables=["job_text"],
    template="""
    Eres un asistente experto en extracción de datos. A partir del texto de una página web de una oferta de empleo, extrae la siguiente información y devuélvela en formato JSON válido. Si algún campo no está disponible, usa "N/A". Identifica las habilidades o requisitos técnicos mencionados.

    Campos a extraer:
    - title: Título del puesto
    - company: Nombre de la empresa
    - description: Descripción general del puesto
    - location: Ubicación del empleo (puede incluir "Remoto" o detalles)
    - salary: Salario (si está especificado, de lo contrario "Not specified")
    - date_posted: Fecha de publicación
    - job_type: Tipo de empleo (ej. Full time, Part time)
    - requirements: Lista de habilidades o requisitos (ej. ["Python", "React", "5 años de experiencia"])

    Texto de la página:
    {job_text}

    Devuelve SOLO un objeto JSON válido, sin texto adicional, comentarios ni formato markdown. Ejemplo:
    {{"title":"Ejemplo","company":"N/A","description":"N/A","location":"N/A","salary":"Not specified","date_posted":"N/A","job_type":"N/A","requirements":["N/A"]}}
    """
)

# Cadena de LangChain
chain = prompt_template | llm | StrOutputParser()

async def extract_job_links(html):
    """Extrae los enlaces de las ofertas de empleo desde el HTML."""
    soup = BeautifulSoup(html, "html.parser")
    job_links = []
    for a_tag in soup.find_all("a", class_="gb-results-list__item"):
        href = a_tag.get("href")
        if href and "/jobs/" in href:
            full_url = f"https://www.getonbrd.com{href}" if href.startswith("/") else href
            job_links.append(full_url)
    return job_links

async def extract_job_details(crawler, url):
    """Extrae el texto de una oferta de empleo con BeautifulSoup y lo procesa con un LLM."""
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=None,
        delay_before_return_html=8.0
    )
    
    result = await crawler.arun(url, config=run_config)
    
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

async def main():
    browser_config = BrowserConfig(
        headless=True,
        verbose=True
    )
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        # Scrapear la página principal
        run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            extraction_strategy=None,
            delay_before_return_html=8.0
        )
        
        result = await crawler.arun(URL, config=run_config)
        
        if not result.success:
            print(f"❌ Falló el scraping de la página principal: {result.error_message}")
            return
        
        # Guardar el HTML de la página principal para inspección
        with open(OUTPUT_DIR / "debug_getonboard.html", "w", encoding="utf-8") as f:
            f.write(result.html)
        
        # Extraer enlaces de las ofertas
        job_links = await extract_job_links(result.html)
        print(f"📋 Encontrados {len(job_links)} enlaces de ofertas de empleo")
        
        if not job_links:
            print("⚠️ No se encontraron enlaces. Revisa el HTML en output/debug_getonboard.html")
            return
        
        # Limitar a los 3 primeros enlaces para pruebas
        job_links = job_links[:3]
        print(f"🔍 Scraping los primeros {len(job_links)} enlaces para pruebas")
        
        # Scrapear cada oferta
        jobs = []
        for i, link in enumerate(job_links, 1):
            print(f"🔍 Scraping oferta {i}/{len(job_links)}: {link}")
            job_details = await extract_job_details(crawler, link)
            if job_details:
                jobs.append(job_details)
            await asyncio.sleep(1.5)
        
        # Guardar los resultados en un JSON
        with open(OUTPUT_DIR / "jobs_getonboard.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"✅ Resultados guardados en {OUTPUT_DIR / 'jobs_getonboard.json'}")

if __name__ == "__main__":
    asyncio.run(main())