"""
evaluate_llm.py
Compare 2 prompt strategies with LLM-as-judge.

Usage:
  python eval/evaluate_llm.py
"""

import json
import os
import sys
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import anthropic
from dotenv import load_dotenv
load_dotenv()

from search.minsearch import Index
from search.hybrid import hybrid_search
from ingestion.embedder import Embedder
from agent.rag import PROMPT_A, PROMPT_B, generate_answer

CHUNKS_PATH = "data/chunks.json"
GROUND_TRUTH_PATH = "eval/ground_truth.json"
SAMPLE_SIZE = 20
OUTPUT_PATH = "eval/llm_eval_results.json"

JUDGE_PROMPT = """Rate this job market assistant answer (1-5):

Question: {question}
Context: {context}
Answer: {answer}

Return ONLY JSON:
{{"relevance": 4, "faithfulness": 5, "reasoning": "one sentence"}}"""


def judge(question, context, answer, client):
    resp = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=150,
        messages=[{"role": "user", "content": JUDGE_PROMPT.format(
            question=question, context=context[:1500], answer=answer)}]
    )
    try:
        return json.loads(resp.content[0].text)
    except Exception:
        return {"relevance": 0, "faithfulness": 0, "reasoning": "parse error"}


def main():
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

    with open(CHUNKS_PATH) as f:
        chunks = json.load(f)
    with open(GROUND_TRUTH_PATH) as f:
        ground_truth = json.load(f)

    sample = random.sample(ground_truth, min(SAMPLE_SIZE, len(ground_truth)))
    index = Index(text_fields=["text"], keyword_fields=["state", "category", "title"])
    index.fit(chunks)
    embedder = Embedder()
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    results = {"prompt_a": [], "prompt_b": []}

    for i, record in enumerate(sample):
        print(f"[{i+1}/{len(sample)}] {record['title']} at {record['company']}")
        retrieved = hybrid_search(record["question"], index, embedder, num_results=5)
        context = "\n".join(r["text"][:300] for r in retrieved)

        for prompt_key, prompt in [("prompt_a", PROMPT_A), ("prompt_b", PROMPT_B)]:
            result = generate_answer(record["question"], retrieved, client, prompt)
            score = judge(record["question"], context, result["answer"], client)
            results[prompt_key].append(score)

    def avg(scores, key):
        return round(sum(s[key] for s in scores) / len(scores), 3)

    print("\n" + "=" * 50)
    print("LLM EVALUATION RESULTS")
    print("=" * 50)
    for prompt, scores in results.items():
        r = avg(scores, "relevance")
        f = avg(scores, "faithfulness")
        print(f"{prompt} | Relevance: {r} | Faithfulness: {f} | Combined: {round((r+f)/2, 3)}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
