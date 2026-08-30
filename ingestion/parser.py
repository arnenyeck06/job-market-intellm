"""
parser.py
Convert raw job postings into chunks for RAG.
Each job becomes 1-2 chunks depending on description length.
Chunk text combines title + company + location + description
for rich semantic search.
"""

import re
import uuid

CHUNK_WORDS = 250
OVERLAP_WORDS = 50

SKILLS_PATTERNS = [
    "python", "sql", "spark", "kafka", "airflow", "dbt", "docker",
    "kubernetes", "terraform", "aws", "gcp", "azure", "postgres",
    "snowflake", "databricks", "pyspark", "pandas", "numpy",
    "pytorch", "tensorflow", "scikit-learn", "mlflow", "fastapi",
    "git", "linux", "bash", "java", "scala", "go", "rust",
    "looker", "tableau", "power bi", "bigquery", "redshift",
    "pgvector", "elasticsearch", "redis", "mongodb", "cassandra",
    "langchain", "openai", "anthropic", "llm", "rag", "vector",
    "machine learning", "deep learning", "nlp", "computer vision",
    "data pipeline", "etl", "elt", "data warehouse", "data lake",
    "data lakehouse", "feature store", "real-time", "streaming",
    "batch processing", "ci/cd", "github actions", "dagster",
]


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)  # strip HTML
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_skills(text: str) -> list[str]:
    """Extract known tech skills from job description."""
    text_lower = text.lower()
    return [skill for skill in SKILLS_PATTERNS if skill in text_lower]


def build_chunk_text(job: dict, description_slice: str) -> str:
    """Build a rich text representation of the job for embedding."""
    parts = [
        f"Job Title: {job['title']}",
        f"Company: {job['company']}",
        f"Location: {job['location']}",
    ]
    if job.get("salary_min") and job.get("salary_max"):
        parts.append(f"Salary: ${job['salary_min']:,.0f} - ${job['salary_max']:,.0f}")
    if job.get("contract_type"):
        parts.append(f"Contract: {job['contract_type']}")
    if job.get("category"):
        parts.append(f"Category: {job['category']}")
    parts.append(f"Description: {description_slice}")
    return "\n".join(parts)


def chunk_job(job: dict) -> list[dict]:
    """Convert a job posting into 1+ chunks."""
    description = clean_text(job.get("description", ""))
    words = description.split()

    if not words:
        return []

    # Split description into overlapping windows
    desc_chunks = []
    start = 0
    while start < len(words):
        end = min(start + CHUNK_WORDS, len(words))
        desc_chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start += CHUNK_WORDS - OVERLAP_WORDS

    chunks = []
    for idx, desc_slice in enumerate(desc_chunks):
        chunk_text = build_chunk_text(job, desc_slice)
        chunks.append({
            "id": f"{job['id']}_{idx}",
            "job_id": job["id"],
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "state": job.get("state", ""),
            "category": job.get("category", ""),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "text": chunk_text,
            "skills": extract_skills(description),
        })

    return chunks


def parse_jobs(jobs: list[dict]) -> list[dict]:
    """Parse a list of normalized job dicts into chunks."""
    all_chunks = []
    for job in jobs:
        chunks = chunk_job(job)
        all_chunks.extend(chunks)
    return all_chunks
