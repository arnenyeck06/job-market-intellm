"""
query_rewriter.py
Rewrites user queries for better job market retrieval.
"""

import re

JOB_EXPANSIONS = {
    "data engineer": "data engineer pipeline ETL spark kafka airflow dbt",
    "ml engineer": "machine learning engineer pytorch tensorflow scikit-learn mlops",
    "llm": "large language model LLM RAG vector database langchain openai anthropic",
    "salary": "salary compensation pay rate annual",
    "remote": "remote work from home distributed",
    "skills": "skills requirements experience technologies stack",
    "hiring": "hiring jobs openings positions available",
    "python": "python pandas numpy spark pyspark",
    "cloud": "AWS GCP Azure cloud infrastructure terraform",
    "senior": "senior staff principal lead architect",
}


def rewrite_query(query: str, use_llm: bool = False, client=None) -> str:
    expanded = query.lower()
    added_terms = []
    for term, expansion in JOB_EXPANSIONS.items():
        if term in expanded:
            added_terms.append(expansion)

    rewritten = f"{query} {' '.join(added_terms)}" if added_terms else query

    if use_llm and client:
        try:
            response = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=100,
                messages=[{"role": "user", "content": f"""Rewrite this job market question as a search query with relevant keywords.
Return ONLY the rewritten query, no explanation.

Original: {query}
Rewritten:"""}]
            )
            llm_rewrite = response.content[0].text.strip()
            if llm_rewrite:
                return llm_rewrite
        except Exception:
            pass

    return rewritten


if __name__ == "__main__":
    tests = [
        "What skills do data engineers need?",
        "highest paying ML jobs",
        "remote LLM engineer positions",
        "Python data pipeline requirements",
    ]
    for q in tests:
        print(f"Original:  {q}")
        print(f"Rewritten: {rewrite_query(q)}")
        print()
