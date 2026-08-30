"""
rag.py
Job Market Intelligence RAG pipeline.
Retrieves relevant job chunks and generates insights with Claude.
"""

import os
import anthropic

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a Job Market Intelligence Assistant specializing in data engineering and AI roles.

Answer questions based ONLY on the provided job posting excerpts.
Your answers should help job seekers understand:
- What skills are in demand
- Salary ranges and trends
- Which companies are hiring
- Location-based opportunities
- How to position themselves for roles

Always cite specific companies and job titles from the excerpts.
If the excerpts don't contain enough information, say so clearly."""

PROMPT_A = SYSTEM_PROMPT

PROMPT_B = """You are a Job Market Intelligence Assistant specializing in data engineering and AI roles.

Think step by step:
1. Identify the most relevant job postings from the excerpts
2. Extract key patterns — skills, salaries, companies, locations
3. Synthesize insights that directly answer the question

Answer based ONLY on the provided job posting excerpts.
Cite specific companies, roles, and salary ranges when available.
If the excerpts don't contain enough information, say so explicitly."""


def build_context(chunks: list[dict]) -> str:
    parts = []
    for i, c in enumerate(chunks, 1):
        salary = ""
        if c.get("salary_min") and c.get("salary_max"):
            salary = f" | ${c['salary_min']:,.0f}–${c['salary_max']:,.0f}"
        parts.append(
            f"[{i}] {c['title']} at {c['company']} — {c['location']}{salary}\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def generate_answer(query: str, chunks: list[dict], client, system_prompt: str = None) -> dict:
    if not chunks:
        return {"answer": "No relevant job postings found for this query.", "sources": []}

    system = system_prompt or SYSTEM_PROMPT
    context = build_context(chunks)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system,
        messages=[{
            "role": "user",
            "content": f"Job Posting Excerpts:\n{context}\n\nQuestion: {query}"
        }],
    )

    return {
        "answer": response.content[0].text,
        "sources": [
            {"title": c["title"], "company": c["company"],
             "location": c["location"], "salary_min": c.get("salary_min"),
             "salary_max": c.get("salary_max")}
            for c in chunks
        ],
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }


def answer_query(query: str, chunks: list[dict], system_prompt: str = None) -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set.")
    client = anthropic.Anthropic(api_key=api_key)
    return generate_answer(query, chunks, client, system_prompt)
