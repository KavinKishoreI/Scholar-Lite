
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
        # Keep router-level access to paper metadata loaded from db/papers.json.
        papers_path = os.path.join(os.path.dirname(__file__), "..", "db", "papers.json")
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
        if words == [] : 
            return []
        words = prefix.split()
        results = self.inverted_index.searchByWord(words[0])
        for i in range(0, len(words)-1):
            search_result = self.inverted_index.searchByWord(words[i])
            results.intersection_update(search_result)
        
        trie_results = self.trie.searchPrefix(words[-1])
        if len(results) == 0 :
            results.update(trie_results)
        else :
            results.intersection_update(trie_results)
        
        if results is None:
            return []
        else :
            return results 
        
    
    def auto_complete(self, prefix, k:int ): 
        results =self.search(prefix)
        min_heap = MinHeap(k)

        for i in results:
            min_heap.insert(self.inverted_index.searchById(i))
        
        topk=  min_heap.getTopK()
        if topk is None: 
            return []
        else: 
            return topk
    
if __name__ == "__main__":
    t1 = time.time()
    query_router= QueryRouter()
    
    results = query_router.auto_complete("machine learning algorithms and analysis", 5)
    t2 = time.time()
    print(len(results), "First search + Startup time", t2 - t1)

    t1 = time.time()
    
    results = query_router.auto_complete("sample analysis", 5)
    t2 = time.time()
    print(len(results), "second search + Startup time", t2 - t1)    
    