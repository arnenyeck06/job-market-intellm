from search.minsearch import Index
from search.vector_store import vector_search as pgvector_search


def rrf(result_lists, k=60, num_results=5):
    scores = {}
    docs = {}
    for results in result_lists:
        for rank, doc in enumerate(results):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
            docs[doc_id] = doc
    ranked = sorted(scores, key=scores.get, reverse=True)
    return [{**docs[d], "_rrf_score": round(scores[d], 6)} for d in ranked[:num_results]]


def hybrid_search(query, index, embedder, state=None, category=None, num_results=5, k=60):
    keyword_results = index.search(query, num_results=num_results * 2)
    q_vec = embedder.encode(query)
    vector_results = pgvector_search(q_vec, state=state, category=category, num_results=num_results * 2)
    return rrf([keyword_results, vector_results], k=k, num_results=num_results)
