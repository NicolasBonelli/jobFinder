from pathlib import Path
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
from dotenv import load_dotenv
import os

# Cargar variables de entorno desde .env
load_dotenv()

# Variables de entorno (serán secrets en GitHub Actions)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
BUCKET_NAME = os.getenv("BUCKET_NAME")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")

# Verificar variables críticas
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY no está definida")
if not BUCKET_NAME:
    raise ValueError("BUCKET_NAME no está definida")

# Configuración de S3
PROFILES_PREFIX = "profiles/"  # Carpeta donde n8n guarda perfiles
RESULTS_PREFIX = "results/"    # Carpeta donde guardamos resultados
JOBS_KEY = "jobs/latest.json"  # Archivo con todos los jobs scrapeados

# URL inicial
URL = "https://www.getonbrd.com/jobs-remote"

# Configuración del navegador para Crawl4AI
BROWSER_CONFIG = BrowserConfig(
    headless=True,
    verbose=True
)

# Configuración de ejecución para Crawl4AI
RUN_CONFIG = CrawlerRunConfig(
    cache_mode=CacheMode.BYPASS,
    extraction_strategy=None,
    delay_before_return_html=1.0
)

# Directorios locales (temporales)
LOCAL_PROFILES_DIR = Path("profiles")
LOCAL_RESULTS_DIR = Path("results")
LOCAL_PROFILES_DIR.mkdir(exist_ok=True)
LOCAL_RESULTS_DIR.mkdir(exist_ok=True)