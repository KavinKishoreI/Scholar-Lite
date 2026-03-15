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
            "this", "it", "its", "as", "into", "through", "during"
        } 
        for i in papers:
            self.map[i['id']] = i
            for word in self.clean_words(i.get('title', '')):
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

    def searchByWord(self, word):
        #Recieves one word and returns set of papers. 
        tokens = self.clean_words(word)
        
        if not tokens or tokens[0] in self.stopWords:
            return set()
        
        return self.index.get(tokens[0], set())


if __name__ == "__main__":
    import json 
    with open("../db/papers.json") as f:
        papers = json.load(f)
    
    idx = InvertedIndex(papers)
    print(idx.searchByWord("machine"))
