import asyncio
import json
import os
import boto3
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler
from config import URL, BROWSER_CONFIG, RUN_CONFIG
from llm import get_llm_chain
from crawler import extract_job_links, extract_job_details

load_dotenv()

BUCKET_NAME = os.getenv("BUCKET_NAME")
s3 = boto3.client("s3")


async def main():
    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        # Scrapear la página principal
        result = await crawler.arun(URL, config=RUN_CONFIG)

        if not result.success:
            print(f"❌ Falló el scraping de la página principal: {result.error_message}")
            return

        # Extraer enlaces de las ofertas
        job_links = await extract_job_links(result.html)
        print(f"📋 Encontrados {len(job_links)} enlaces de ofertas de empleo")

        if not job_links:
            print("⚠️ No se encontraron enlaces. Revisa el HTML.")
            return

        # Obtener la cadena de LangChain/Gemini
        chain = get_llm_chain()

        # Scrapear cada oferta
        jobs = []
        for i, link in enumerate(job_links, 1):
            print(f"🔍 Scraping oferta {i}/{len(job_links)}: {link}")
            job_details = await extract_job_details(crawler, link, chain)
            if job_details:
                jobs.append(job_details)
            await asyncio.sleep(0.5)#Reduci el tiempo

        # Serializar el resultado a JSON
        jobs_json = json.dumps(jobs, ensure_ascii=False, indent=2)

        # Guardar en S3
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key="jobs/latest.json",
            Body=jobs_json.encode("utf-8"),
            ContentType="application/json"
        )
        print(f"✅ {len(jobs)} trabajos guardados correctamente en jobs/latest.json")

if __name__ == "__main__":
    asyncio.run(main())
