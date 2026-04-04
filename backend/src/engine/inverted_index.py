import json
import re

class InvertedIndex:
    def __init__(self, papers):
        self.index = {}
        self.map = {}
        self.stopWords = {
            "a", "an", "the", "and", "or", "but", "in", "on",
            "at", "to", "for", "of", "with", "by", "from", "is",
            "was", "are", "were", "be", "been", "being", "that",
            "this", "it", "its", "as", "into", "through", "during", "none"
        } 
        for doc in papers:
            doc_id = doc.get("id")
            if not doc_id:
                continue

            self.map[doc_id] = doc

            title = doc.get("title") or ""
            abstract = doc.get("abstract") or ""
            text_for_indexing = doc.get("text_for_indexing") or ""

            # Prefer title + abstract; fall back to title + text_for_indexing when abstract is missing.
            if abstract.strip():
                text_blob = f"{title} {abstract}"
            else:
                text_blob = f"{title} {text_for_indexing}"

            cleaned_words = self.clean_words(text_blob)

            for word in cleaned_words:
                if word in self.stopWords:
                    continue
                bucket = self.index.setdefault(word, set())
                bucket.add(doc_id)
      
    def clean_words(self, text):
        # Keep only alphabetic tokens and normalize to lowercase.
       
        return re.findall(r"[a-zA-Z]+", text.lower())

    def searchById(self, paper_id):
        #search by id return full paper documents
        return self.map.get(paper_id)

    def searchByWord(self, token):
        # Receives one normalized word and returns a copy of matching paper ids.
        if not token or not isinstance(token, str):
            return set()

        token = token.lower()
        if token in self.stopWords:
            return set()

        return set(self.index.get(token, set()))


if __name__ == "__main__":
    import json 
    with open("../db/papers.json") as f:
        papers = json.load(f)
    
    idx = InvertedIndex(papers)
    print(idx.searchByWord("learning"))
