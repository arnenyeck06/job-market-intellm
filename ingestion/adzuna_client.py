"""
adzuna_client.py
Fetch job postings from Adzuna API.
Free tier: 250 requests/month, up to 50 results per request.
Sign up: https://developer.adzuna.com/

Set in .env:
  ADZUNA_APP_ID=your_app_id
  ADZUNA_API_KEY=your_api_key
"""

import os
import time
import requests

BASE_URL = "https://api.adzuna.com/v1/api/jobs"

CATEGORIES = [
    "it-jobs",
    "engineering-jobs",
    "science-jobs",
    "accounting-finance-jobs",
]

DE_KEYWORDS = [
    "data engineer",
    "data scientist",
    "machine learning engineer",
    "AI engineer",
    "analytics engineer",
    "data architect",
    "MLOps engineer",
    "LLM engineer",
]


def get_jobs(
    keyword: str,
    country: str = "us",
    page: int = 1,
    results_per_page: int = 50,
    location: str = None,
    category: str = None,
) -> dict:
    app_id = os.getenv("ADZUNA_APP_ID")
    api_key = os.getenv("ADZUNA_API_KEY")

    if not app_id or not api_key:
        raise EnvironmentError("Set ADZUNA_APP_ID and ADZUNA_API_KEY in .env")

    params = {
        "app_id": app_id,
        "app_key": api_key,
        "results_per_page": results_per_page,
        "what": keyword,
        "content-type": "application/json",
    }

    if location:
        params["where"] = location
    if category:
        params["category"] = category

    url = f"{BASE_URL}/{country}/search/{page}"
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_all_keywords(
    keywords: list[str] = None,
    country: str = "us",
    pages: int = 2,
    delay: float = 1.0,
) -> list[dict]:
    keywords = keywords or DE_KEYWORDS
    all_jobs = {}  # dedup by job id

    for keyword in keywords:
        print(f"[adzuna] Fetching: {keyword}")
        for page in range(1, pages + 1):
            try:
                data = get_jobs(keyword, country=country, page=page)
                results = data.get("results", [])
                for job in results:
                    job_id = job.get("id")
                    if job_id and job_id not in all_jobs:
                        all_jobs[job_id] = job
                print(f"  page {page}: {len(results)} jobs (total unique: {len(all_jobs)})")
                time.sleep(delay)
            except Exception as e:
                print(f"  ERROR page {page}: {e}")
                time.sleep(5)

    return list(all_jobs.values())


def normalize_job(job: dict) -> dict:
    """Normalize Adzuna job response to our schema."""
    location = job.get("location", {})
    salary = job.get("salary_min"), job.get("salary_max")

    return {
        "id": job.get("id", ""),
        "title": job.get("title", ""),
        "company": job.get("company", {}).get("display_name", ""),
        "location": location.get("display_name", ""),
        "state": _extract_state(location),
        "country": "us",
        "salary_min": salary[0],
        "salary_max": salary[1],
        "contract_type": job.get("contract_type", ""),
        "category": job.get("category", {}).get("label", ""),
        "description": job.get("description", ""),
        "url": job.get("redirect_url", ""),
        "created": job.get("created", ""),
    }


def _extract_state(location: dict) -> str:
    """Extract US state from location area array."""
    areas = location.get("area", [])
    if len(areas) >= 2:
        return areas[-2]  # typically state is second to last
    return ""
