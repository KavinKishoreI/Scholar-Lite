
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
    
    def search(self, prefix ):
        words = self.clean_words(prefix)
        if not words:
            return set()
        if all(word in self.inverted_index.stopWords for word in words):
            return set()

        results = self.inverted_index.searchByWord(words[0])
        for i in range(1, len(words)):
            search_result = self.inverted_index.searchByWord(words[i])
            results.intersection_update(search_result)
        
        trie_results = (
            self.trie.searchPrefix(words[-1])
            if words[-1] not in self.inverted_index.stopWords
            else set()
        )
        if len(results) == 0 :
            results.update(trie_results)
        else :
            results.intersection_update(trie_results)
        
        if results is None:
            return []
        else :
            return results 
        
    
    def auto_complete(self, prefix, k:int ): 
        results = self.search(prefix)
        if not results:
            return []

        min_heap = MinHeap(k)

        for i in results:
            paper = self.inverted_index.searchById(i)
            if paper is not None:
                min_heap.insert(paper)
        
        topk=  min_heap.getTopK()
        if topk is None: 
            return []
        else: 
            return topk
    
if __name__ == "__main__":
    t1 = time.time()
    query_router= QueryRouter()
    
    results = query_router.auto_complete("mach", 100)
    t2 = time.time()
    
    print(len(results))
    print("first search : ", t2- t1)

    