
from objects import papers, invertedIndex, prefix_tree
from minheap import MinHeap
import re 
import json 
import os
import time
class QueryRouter: 
    def __init__(self):
        self.inverted_index = invertedIndex
        self.trie = prefix_tree
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
    
    def _search(self, prefix):
        """Strict AND over query tokens via inverted index; trie left for autocomplete only."""
        words = self.clean_words(prefix)
        if not words:
            return set()

        # Remove stopwords for search logic.
        words = [w for w in words if w not in self.inverted_index.stopWords]
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

    def search_ranked(self, prefix, limit: int = 10, offset: int = 0):
        """Strict AND search ranked by recency (then citations) with pagination."""
        matches = self._search(prefix)
        if not matches:
            return {"total": 0, "results": []}

        start = max(0, offset)
        page_size = max(0, limit)
        page_end = start + page_size
        total = len(matches)
        if page_end == 0:
            return {"total": total, "results": []}

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
        return {"total": total, "results": ranked_prefix[start:page_end]}
        
    
    def auto_complete(self, prefix, k:int ): 
        words = [w for w in self.clean_words(prefix) if w not in self.inverted_index.stopWords]
        if not words:
            return []

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
            return []

        min_heap = MinHeap(k)
        for doc_id in candidates:
            paper = self.inverted_index.searchById(doc_id)
            if paper is not None:
                min_heap.insert(paper)

        topk = min_heap.getTopK()
        return topk or []
    
if __name__ == "__main__":
    qr = QueryRouter()
    tests = [
        ("deep learning", 0, 5),
       # ("deep learning", 100, 5),
       # ("graph neural", 200, 5),
       # ("transformer", 10, 5),
        
    ]

    print("=== search_ranked (paginated) ===")
    for q, offset, k in tests:
        t0 = time.time()
        res = qr.search_ranked(q, limit=k, offset=offset)
        dt = time.time() - t0
        print(f"query={q!r} offset={offset} limit={k}")
        print(f"total={res['total']} returned={len(res['results'])} time={dt:.4f}s")
        for idx, paper in enumerate(res["results"], start=1):
            print(f"{idx}. {paper.get('title')} ({paper.get('year')})")
        print()

    print("\n=== auto_complete (year-ranked) ===")
    for q, _, k in tests:
        t0 = time.time()
        res = qr.auto_complete(q, k)
        dt = time.time() - t0
        print(f"query={q!r} limit={k}")
        print(f"count={len(res)} time={dt:.4f}s")
        for idx, paper in enumerate(res, start=1):
            print(f"{idx}. {paper.get('title')} ({paper.get('year')})")
        print()

    
