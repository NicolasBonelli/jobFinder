import asyncio
import json
import os
import boto3
from crawl4ai import AsyncWebCrawler
from config import URL, BROWSER_CONFIG, RUN_CONFIG , BUCKET_NAME, OUTPUT_KEY
from crawler import extract_job_links, extract_job_details
from llm import get_llm_chain

s3 = boto3.client("s3")


async def run_scraper():
    async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
        # 1. Scrappear página principal
        result = await crawler.arun(URL, config=RUN_CONFIG)

        if not result.success:
            print(f"❌ Falló el scraping: {result.error_message}")
            return []

        # 2. Extraer enlaces
        job_links = await extract_job_links(result.html)
        print(f"📋 {len(job_links)} ofertas encontradas")

        if not job_links:
            print("⚠️ No se encontraron enlaces.")
            return []

        # 3. Obtener LLM de LangChain
        chain = get_llm_chain()

        # 4. Scrappear cada oferta
        jobs = []
        for i, link in enumerate(job_links, 1):
            print(f"🔍 Scraping {i}/{len(job_links)}: {link}")
            job_details = await extract_job_details(crawler, link, chain)
            if job_details:
                jobs.append(job_details)
            await asyncio.sleep(1.0)  # para evitar baneos

        return jobs

def lambda_handler(event, context):
    jobs = asyncio.run(run_scraper())

    if not jobs:
        return {
            "statusCode": 500,
            "body": "No se pudieron scrappear trabajos."
        }

    # Subir a S3 en lugar de guardar en disco
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=OUTPUT_KEY,
        Body=json.dumps(jobs, ensure_ascii=False, indent=2),
        ContentType="application/json"
    )

    return {
        "statusCode": 200,
        "body": f"{len(jobs)} trabajos guardados correctamente en S3."
    }
