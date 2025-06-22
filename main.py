import asyncio
import json
from crawl4ai import AsyncWebCrawler
from config import URL, BROWSER_CONFIG, RUN_CONFIG, OUTPUT_DIR
from llm import get_llm_chain
from crawler import extract_job_links, extract_job_details

async def main():
    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        # Scrapear la página principal
        result = await crawler.arun(URL, config=RUN_CONFIG)
        
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
        
        # Obtener la cadena de LangChain
        chain = get_llm_chain()
        
        # Scrapear cada oferta
        jobs = []
        for i, link in enumerate(job_links, 1):
            print(f"🔍 Scraping oferta {i}/{len(job_links)}: {link}")
            job_details = await extract_job_details(crawler, link, chain)
            if job_details:
                jobs.append(job_details)
            await asyncio.sleep(1.5)
        
        # Guardar los resultados en un JSON
        with open(OUTPUT_DIR / "jobs_getonboard.json", "w", encoding="utf-8") as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        print(f"✅ Resultados guardados en {OUTPUT_DIR / 'jobs_getonboard.json'}")

if __name__ == "__main__":
    asyncio.run(main())