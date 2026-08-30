"""
db_loader.py
Load normalized job postings into Postgres.
"""

import os
import psycopg2
import psycopg2.extras


def get_conn():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5434"),
        dbname=os.getenv("POSTGRES_DB", "job_market"),
        user=os.getenv("POSTGRES_USER", "jobs"),
        password=os.getenv("POSTGRES_PASSWORD", "jobs123"),
    )


def upsert_job(job: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO jobs (id, title, company, location, state, country,
                          salary_min, salary_max, contract_type, category,
                          description, url, created)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            salary_min = EXCLUDED.salary_min,
            salary_max = EXCLUDED.salary_max
    """, (
        job["id"], job["title"], job["company"], job["location"],
        job["state"], job["country"], job["salary_min"], job["salary_max"],
        job["contract_type"], job["category"], job["description"],
        job["url"], job["created"],
    ))
    conn.commit()
    cur.close()
    conn.close()


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]):
    conn = get_conn()
    cur = conn.cursor()
    for chunk, embedding in zip(chunks, embeddings):
        cur.execute("""
            INSERT INTO chunks (id, job_id, title, company, location, state,
                                category, salary_min, salary_max, text, embedding)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::vector)
            ON CONFLICT (id) DO UPDATE SET
                text = EXCLUDED.text,
                embedding = EXCLUDED.embedding
        """, (
            chunk["id"], chunk["job_id"], chunk["title"], chunk["company"],
            chunk["location"], chunk["state"], chunk["category"],
            chunk["salary_min"], chunk["salary_max"],
            chunk["text"], str(embedding),
        ))
    conn.commit()
    cur.close()
    conn.close()


def get_job_count() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM jobs")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count


def get_chunk_count() -> int:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM chunks")
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count
