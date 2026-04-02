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
        for i in papers:
            self.map[i['id']] = i
            cleaned_words = self.clean_words(i.get('title') or  '')
            
            for word in cleaned_words:
                if word in self.stopWords: 
                    continue
                if word not in self.index:
                    self.index[word] = set()
                self.index[word].add(i['id'])
      
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
