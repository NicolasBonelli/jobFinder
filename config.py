from pathlib import Path
from crawl4ai import BrowserConfig, CrawlerRunConfig, CacheMode
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