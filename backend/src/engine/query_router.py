
from objects import papers, invertedIndex, prefix_tree, search_cache, autocomplete_cache
from minheap import MinHeap
import re 
import json 
import os
import time
class QueryRouter: 
    def __init__(self):
        self.inverted_index = invertedIndex
        self.trie = prefix_tree
        self.search_cache = search_cache
        self.autocomplete_cache = autocomplete_cache
        self.papers = self.load_papers()

    def load_papers(self):
        # Keep router-level access to paper metadata loaded from db/semantic_scholar_papers.json.
        papers_path = os.path.join(os.path.dirname(__file__), "..", "db", "semantic_scholar_papers.json")
        try:
            with open(os.path.abspath(papers_path), "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return papers
        
    def clean_words(self, text):
        # Keep only alphabetic tokens and normalize to lowercase.
        return re.findall(r"[a-zA-Z]+", text.lower())

    def _normalized_words(self, text):
        return [w for w in self.clean_words(text) if w not in self.inverted_index.stopWords]

    def _search_words(self, words):
        if not words:
            return set()

        results = None
        for w in words:
            hits = self.inverted_index.searchByWord(w)
            if not hits:
                return set()
            results = hits if results is None else results.intersection(hits)
            if not results:
                return set()

        return results or set()
    
    def _search(self, prefix):
        """Strict AND over query tokens via inverted index; trie left for autocomplete only."""
        words = self._normalized_words(prefix)
        return self._search_words(words)

    def search_ranked(self, prefix, limit: int = 10, offset: int = 0):
        """Strict AND search ranked by recency (then citations) with pagination."""
        start = max(0, offset)
        page_size = max(0, limit)
        page_end = start + page_size
        words = self._normalized_words(prefix)
        cache_key = (" ".join(words), start, page_size)

        cached_result = self.search_cache.get(cache_key)
        if cached_result is not None:
            return {"total": cached_result["total"], "results": list(cached_result["results"])}

        matches = self._search_words(words)
        if not matches:
            result = {"total": 0, "results": []}
            self.search_cache.put(cache_key, result)
            return result

        total = len(matches)
        if page_end == 0:
            result = {"total": total, "results": []}
            self.search_cache.put(cache_key, result)
            return result

        def rank_key(doc):
            return (
                int(doc.get("year") or 0),
                int(doc.get("citation_count") or doc.get("cited_by_count") or 0),
                doc.get("id") or "",
            )

        min_heap = MinHeap(page_end, key_fn=rank_key)
        for doc_id in matches:
            paper = self.inverted_index.searchById(doc_id)
            if paper is not None:
                min_heap.insert(paper)

        ranked_prefix = min_heap.getTopK()
        result = {"total": total, "results": ranked_prefix[start:page_end]}
        self.search_cache.put(cache_key, result)
        return {"total": total, "results": list(result["results"])}
        
    
    def auto_complete(self, prefix, k:int ): 
        words = self._normalized_words(prefix)
        if not words:
            return []

        cache_key = (" ".join(words), max(0, k))
        cached_result = self.autocomplete_cache.get(cache_key)
        if cached_result is not None:
            return list(cached_result)

        # If only one token, use trie prefix results; else AND the preceding tokens, then prefix-match last.
        if len(words) == 1:
            candidates = self.trie.searchPrefix(words[0])
        else:
            base_tokens = words[:-1]
            last = words[-1]
            base_hits = None
            for w in base_tokens:
                hits = self.inverted_index.searchByWord(w)
                if not hits:
                    return []
                base_hits = hits if base_hits is None else base_hits.intersection(hits)
                if not base_hits:
                    return []
            trie_hits = self.trie.searchPrefix(last) if last not in self.inverted_index.stopWords else set()
            candidates = base_hits.intersection(trie_hits) if trie_hits else set()

        if not candidates:
            self.autocomplete_cache.put(cache_key, [])
            return []

        min_heap = MinHeap(k)
        for doc_id in candidates:
            paper = self.inverted_index.searchById(doc_id)
            if paper is not None:
                min_heap.insert(paper)

        topk = min_heap.getTopK()
        result = topk or []
        self.autocomplete_cache.put(cache_key, result)
        return list(result)
    
if __name__ == "__main__":
    qr = QueryRouter()
    tests = [
        ("deep learning", 0, 5),
        ("langchain", 5, 5),
        ("network", 5, 5),
        ("machine learning", 0, 5),
        ("deep learning", 5, 5),
        ("graph neural", 0, 5),
        ("deep learning", 0, 5),
        ("network", 5, 5),
        ("data analysis", 0, 5),
    ]

    def timed_call(fn, *args, **kwargs):
        start_time = time.time()
        result = fn(*args, **kwargs)
        elapsed = time.time() - start_time
        return result, elapsed

    print("\n=== cache verification ===")

    query = "deep learning"
    print(f"initial search_cache_size={len(qr.search_cache)}")
    first_page, first_page_time = timed_call(qr.search_ranked, query, limit=5, offset=0)
    print(f"after search page 1 -> search_cache_size={len(qr.search_cache)}")
    first_page_repeat, first_page_repeat_time = timed_call(qr.search_ranked, query, limit=5, offset=0)
    print(f"after repeating page 1 -> search_cache_size={len(qr.search_cache)}")
    second_page, second_page_time = timed_call(qr.search_ranked, query, limit=5, offset=5)
    print(f"after search page 2 -> search_cache_size={len(qr.search_cache)}")
    print(
        "search cache checks:",
        {
            "same_page_same_results": [p.get("title") for p in first_page["results"]]
            == [p.get("title") for p in first_page_repeat["results"]],
            "page_1_vs_page_2_different": [p.get("title") for p in first_page["results"]]
            != [p.get("title") for p in second_page["results"]],
            "total_hits_consistent": first_page["total"]
            == first_page_repeat["total"]
            == second_page["total"],
            "times_sec": {
                "page_1_first_call": round(first_page_time, 6),
                "page_1_repeat_call": round(first_page_repeat_time, 6),
                "page_2_call": round(second_page_time, 6),
            },
        },
    )

    print(f"\ninitial autocomplete_cache_size={len(qr.autocomplete_cache)}")
    auto_first, auto_first_time = timed_call(qr.auto_complete, query, 5)
    print(f"after autocomplete top 5 -> autocomplete_cache_size={len(qr.autocomplete_cache)}")
    auto_first_repeat, auto_first_repeat_time = timed_call(qr.auto_complete, query, 5)
    print(f"after repeating top 5 -> autocomplete_cache_size={len(qr.autocomplete_cache)}")
    auto_three, auto_three_time = timed_call(qr.auto_complete, query, 3)
    print(f"after autocomplete top 3 -> autocomplete_cache_size={len(qr.autocomplete_cache)}")
    print(
        "autocomplete cache checks:",
        {
            "same_key_same_results": [p.get("title") for p in auto_first]
            == [p.get("title") for p in auto_first_repeat],
            "different_k_new_entry": len(qr.autocomplete_cache) >= 2,
            "counts": [len(auto_first), len(auto_first_repeat), len(auto_three)],
            "times_sec": {
                "top_5_first_call": round(auto_first_time, 6),
                "top_5_repeat_call": round(auto_first_repeat_time, 6),
                "top_3_call": round(auto_three_time, 6),
            },
        },
    )

    print("=== search_ranked (paginated) ===")
    for q, offset, k in tests:
        res, dt = timed_call(qr.search_ranked, q, limit=k, offset=offset)
        print(f"query={q!r} offset={offset} limit={k}")
        print(f"total={res['total']} returned={len(res['results'])} time={dt:.4f}s")
        #for idx, paper in enumerate(res["results"], start=1):
         #   print(f"{idx}. {paper.get('title')} ({paper.get('year')})")
        #print()

    print("\n=== auto_complete (year-ranked) ===")
    for q, _, k in tests:
        res, dt = timed_call(qr.auto_complete, q, k)
        print(f"query={q!r} limit={k}")
        print(f"count={len(res)} time={dt:.4f}s")
        #for idx, paper in enumerate(res, start=1):
         #   print(f"{idx}. {paper.get('title')} ({paper.get('year')})")
        #print()

    
