"""
query.py — CLI for Job Market Intelligence Assistant.

Usage:
  python query.py "what skills do data engineering roles require"
  python query.py "highest paying ML jobs" --state "California"
  python query.py "what companies are hiring DE roles" --search hybrid
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()

from search.minsearch import Index
from search.hybrid import hybrid_search
from search.vector_store import vector_search
from agent.rag import answer_query

CHUNKS_PATH = "data/chunks.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Job market question")
    parser.add_argument("--state", help="Filter by state e.g. Minnesota")
    parser.add_argument("--category", help="Filter by job category")
    parser.add_argument("--search", choices=["keyword", "vector", "hybrid"], default="hybrid")
    parser.add_argument("--num-results", type=int, default=5)
    args = parser.parse_args()

    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)

    index = Index(text_fields=["text"], keyword_fields=["state", "category", "title"])
    index.fit(chunks)

    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    if args.search == "keyword":
        filter_dict = {}
        if args.state:
            filter_dict["state"] = args.state
        retrieved = index.search(args.query, filter_dict=filter_dict, num_results=args.num_results)
    elif args.search == "vector":
        from ingestion.embedder import Embedder
        embedder = Embedder()
        q_vec = embedder.encode(args.query)
        retrieved = vector_search(q_vec, state=args.state, category=args.category, num_results=args.num_results)
    else:
        from ingestion.embedder import Embedder
        embedder = Embedder()
        retrieved = hybrid_search(
            query=args.query, index=index, embedder=embedder,
            state=args.state, category=args.category, num_results=args.num_results,
        )

    print(f"[query] Retrieved {len(retrieved)} chunks via {args.search} search.")

    result = answer_query(args.query, retrieved)

    print("\n" + "=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(result["answer"])
    print("\n" + "-" * 60)
    print("SOURCES")
    print("-" * 60)
    for s in result["sources"]:
        salary = f" ${s['salary_min']:,.0f}–${s['salary_max']:,.0f}" if s.get("salary_min") else ""
        print(f"  {s['title']} at {s['company']} — {s['location']}{salary}")
    print(f"\n[tokens] in={result.get('input_tokens','?')} out={result.get('output_tokens','?')}")


if __name__ == "__main__":
    main()
