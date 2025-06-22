import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher
from crawl4ai import CrawlerMonitor, RateLimiter
import json
from pathlib import Path

from bs4 import BeautifulSoup

# URLs por sitio
URLS = {
    "getonboard": "https://www.getonbrd.com/jobs-remote",
    "mappa": "https://mappa.ai/jobs?remote=true",
    "remoteok": "https://remoteok.com/remote-dev-jobs"
}

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

async def fetch_all():
    browser_cfg = BrowserConfig(headless=True)
    run_cfg = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        extraction_strategy=None
    )
    dispatcher = MemoryAdaptiveDispatcher(
        memory_threshold_percent=75.0,
        max_session_permit=5,
        rate_limiter=RateLimiter(base_delay=(1.0, 2.0), max_retries=2),
        monitor=CrawlerMonitor(display_mode=CrawlerMonitor.DisplayMode.AGGREGATED)
    )

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        results = await crawler.arun_many(
            urls=list(URLS.values()),
            config=run_cfg,
            dispatcher=dispatcher
        )

        for job_name, result in zip(URLS.keys(), results):
            if not result.success:
                print(f"❌ Falló {job_name}: {result.error_message}")
                continue

            soup = BeautifulSoup(result.clean_html, "html.parser")
            data = []

            # 🔹 GetOnBoard
            if job_name == "getonboard":
                for job in soup.select("article.job"):
                    data.append({
                        "titulo": job.select_one("h2 a").text.strip(),
                        "link": "https://www.getonbrd.com" + job.select_one("h2 a")["href"],
                        "empresa": job.select_one(".gb-company span").text.strip(),
                        "descripcion": job.select_one(".gb-description").text.strip(),
                        "modalidad": job.select_one(".tags li").text.strip() if job.select_one(".tags li") else "N/A"
                    })

            # 🔹 Mappa.ai
            elif job_name == "mappa":
                for card in soup.select("a.job-card"):
                    data.append({
                        "titulo": card.select_one("h3").text.strip(),
                        "link": "https://mappa.ai" + card["href"],
                        "empresa": card.select_one(".text-gray-500").text.strip() if card.select_one(".text-gray-500") else "Mappa",
                        "descripcion": card.select_one(".text-sm.text-gray-700").text.strip() if card.select_one(".text-sm.text-gray-700") else "Sin descripción",
                        "modalidad": "Remote" if "remote" in card.text.lower() else "On-site"
                    })

            # 🔹 RemoteOK
            elif job_name == "remoteok":
                for row in soup.select("tr.job"):
                    if not row.get("data-url"):
                        continue
                    data.append({
                        "titulo": row.select_one("h2").text.strip() if row.select_one("h2") else "Sin título",
                        "link": "https://remoteok.com" + row["data-url"],
                        "empresa": row["data-company"] if row.get("data-company") else "Desconocida",
                        "descripcion": row["data-tags"] if row.get("data-tags") else "Sin descripción",
                        "modalidad": "Remote"
                    })

            # Guardar resultados por sitio
            out_path = OUTPUT_DIR / f"{job_name}.json"
            with open(out_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"✅ {job_name}: {len(data)} ofertas guardadas en {out_path}")

if __name__ == "__main__":
    asyncio.run(fetch_all())
