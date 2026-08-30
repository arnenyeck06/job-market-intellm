"""
generate_ground_truth.py
Generate ground truth Q&A pairs for retrieval evaluation.

Usage:
  python eval/generate_ground_truth.py
"""

import json
import os
import random
import anthropic
from dotenv import load_dotenv
load_dotenv()

CHUNKS_PATH = "data/chunks.json"
OUTPUT_PATH = "eval/ground_truth.json"
QUESTIONS_PER_CHUNK = 3
SAMPLE_CHUNKS = 50


def generate_questions(chunk, client):
    prompt = f"""You are evaluating a job market RAG system.

Given this job posting excerpt, generate {QUESTIONS_PER_CHUNK} questions that:
- Are answered directly by this excerpt
- Use different wording than the excerpt
- Sound like real job seeker questions

Job Title: {chunk['title']}
Company: {chunk['company']}
Location: {chunk['location']}

Excerpt:
{chunk['text'][:600]}

Return ONLY a JSON array of {QUESTIONS_PER_CHUNK} questions, no other text.
Example: ["question 1", "question 2", "question 3"]"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    try:
        return json.loads(response.content[0].text)
    except Exception:
        return []


def main():
    os.makedirs("eval", exist_ok=True)
    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)

    sampled = random.sample(chunks, min(SAMPLE_CHUNKS, len(chunks)))
    print(f"Generating questions for {len(sampled)} chunks...")

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    ground_truth = []

    for i, chunk in enumerate(sampled):
        print(f"[{i+1}/{len(sampled)}] {chunk['title']} at {chunk['company']}")
        questions = generate_questions(chunk, client)
        for q in questions:
            ground_truth.append({
                "question": q,
                "chunk_id": chunk["id"],
                "title": chunk["title"],
                "company": chunk["company"],
                "location": chunk["location"],
            })

    with open(OUTPUT_PATH, "w") as f:
        json.dump(ground_truth, f, indent=2)
    print(f"\nGenerated {len(ground_truth)} ground truth pairs → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
