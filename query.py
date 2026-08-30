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
from search.reranker import rerank
from agent.rag import answer_query
from agent.query_rewriter import rewrite_query

CHUNKS_PATH = "data/chunks.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Job market question")
    parser.add_argument("--state", help="Filter by state e.g. Minnesota")
    parser.add_argument("--category", help="Filter by job category")
    parser.add_argument("--search", choices=["keyword", "vector", "hybrid"], default="hybrid")
    parser.add_argument("--num-results", type=int, default=5)
    args = parser.parse_args()

    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)

    index = Index(text_fields=["text"], keyword_fields=["state", "category", "title"])
    index.fit(chunks)

    # Step 1: Query rewriting
    rewritten = rewrite_query(args.query)
    if rewritten != args.query:
        print(f"[rewriter] {args.query} → {rewritten[:80]}...")

    from ingestion.embedder import Embedder
    embedder = Embedder()

    # Step 2: Retrieve
    if args.search == "keyword":
        filter_dict = {}
        if args.state:
            filter_dict["state"] = args.state
        retrieved = index.search(rewritten, filter_dict=filter_dict,
                                num_results=args.num_results * 2)
    elif args.search == "vector":
        q_vec = embedder.encode(rewritten)
        retrieved = vector_search(q_vec, state=args.state,
                                 category=args.category, num_results=args.num_results * 2)
    else:
        retrieved = hybrid_search(
            query=rewritten, index=index, embedder=embedder,
            state=args.state, category=args.category,
            num_results=args.num_results * 2,
        )

    # Step 3: Re-rank
    retrieved = rerank(rewritten, retrieved, embedder, top_n=args.num_results)
    print(f"[query] Retrieved and re-ranked {len(retrieved)} chunks.")

    # Step 4: Generate
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
