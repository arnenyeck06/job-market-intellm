import math
from collections import defaultdict


class Index:
    def __init__(self, text_fields, keyword_fields=None):
        self.text_fields = text_fields
        self.keyword_fields = keyword_fields or []
        self.docs = []
        self.index = defaultdict(lambda: defaultdict(list))
        self.doc_count = 0

    def fit(self, docs):
        self.docs = docs
        self.doc_count = len(docs)
        self.index = defaultdict(lambda: defaultdict(list))
        for doc_id, doc in enumerate(docs):
            for field in self.text_fields:
                for term in set(self._tokenize(doc.get(field, ""))):
                    self.index[term][field].append(doc_id)
        return self

    def search(self, query, filter_dict=None, boost_dict=None, num_results=10):
        filter_dict = filter_dict or {}
        boost_dict = boost_dict or {f: 1.0 for f in self.text_fields}
        scores = defaultdict(float)
        for term in self._tokenize(query):
            for field in self.text_fields:
                if term not in self.index or field not in self.index[term]:
                    continue
                matching = self.index[term][field]
                idf = math.log((self.doc_count + 1) / (len(matching) + 1)) + 1
                for doc_id in matching:
                    scores[doc_id] += idf * boost_dict.get(field, 1.0)
        results = []
        for doc_id, score in sorted(scores.items(), key=lambda x: -x[1]):
            doc = self.docs[doc_id]
            if all(str(doc.get(k, "")).lower() == str(v).lower() for k, v in filter_dict.items()):
                results.append({**doc, "_score": round(score, 4)})
            if len(results) >= num_results:
                break
        return results

    def _tokenize(self, text):
        import re
        return [t for t in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(t) > 2]
