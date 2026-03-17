
from objects import papers, invertedIndex, prefix_tree
from minheap import MinHeap
import re 
import json 
import os
class QueryRouter: 
    def __init__(self, k : int):
        self.inverted_index = invertedIndex()
        self.trie = prefix_tree()
        self.heap = MinHeap(k)
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
        words = self.clean_words(words)
        words = prefix.split()
        results = set()
        for i in range(0, len(words)-1):
            
            search_result = self.inverted_index.searchByWord(words[i])
            if len(results) == 0 :
                results.update(search_result)
            else :
                results.intersection_update(search_result)
        trie_results = self.trie.searchPrefix(words[-1])
        if len(results) == 0 :
            results.update(search_result)
        else :
            results.intersection_update(search_result)
        return results     
        
    
