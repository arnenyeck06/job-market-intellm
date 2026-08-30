"""
ingest.py
Fetch job postings from Adzuna and load into Postgres + pgvector.

Usage:
  python ingest.py
  python ingest.py --keywords "data engineer" "machine learning engineer"
  python ingest.py --pages 3
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from ingestion.adzuna_client import fetch_all_keywords, normalize_job, DE_KEYWORDS
from ingestion.parser import parse_jobs
from ingestion.db_loader import upsert_job, upsert_chunks, get_job_count, get_chunk_count

CHUNKS_PATH = "data/chunks.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs="+", default=DE_KEYWORDS)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--skip-vectors", action="store_true")
    args = parser.parse_args()

    print(f"[ingest] Fetching jobs for {len(args.keywords)} keywords, {args.pages} pages each...")
    raw_jobs = fetch_all_keywords(keywords=args.keywords, pages=args.pages)
    print(f"[ingest] Fetched {len(raw_jobs)} unique job postings.")

    normalized = [normalize_job(j) for j in raw_jobs]

    print("[ingest] Loading jobs into Postgres...")
    for job in normalized:
        upsert_job(job)
    print(f"[ingest] Jobs in DB: {get_job_count()}")

    print("[ingest] Building chunks...")
    chunks = parse_jobs(normalized)
    print(f"[ingest] {len(chunks)} chunks generated.")

    os.makedirs("data", exist_ok=True)
    with open(CHUNKS_PATH, "w") as f:
        json.dump(chunks, f, indent=2)
    print(f"[ingest] Chunks saved to {CHUNKS_PATH}")

    if not args.skip_vectors:
        try:
            from ingestion.embedder import Embedder
            embedder = Embedder()
            print(f"[ingest] Embedding {len(chunks)} chunks...")
            texts = [c["text"] for c in chunks]
            embeddings = embedder.encode_batch(texts).tolist()
            upsert_chunks(chunks, embeddings)
            print(f"[ingest] Upserted {len(chunks)} chunks to pgvector.")
        except Exception as e:
            print(f"[ingest] Embedding skipped: {e}")
    else:
        print("[ingest] Skipping vector upsert.")

    print(f"[ingest] Done. Chunks in DB: {get_chunk_count()}")


if __name__ == "__main__":
    main()
