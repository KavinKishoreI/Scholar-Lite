from typing import List
import re 
class Node : 
    def __init__(self, root: bool= False, terminal : bool = False):
         # enforcing only one character can be used to build a trie. 
        self.children: List[Node] = [None] * 26
        self.root = root
        self.terminal = terminal
        

class Trie:
    
    def validate(self,s): 
        return bool(re.match(r'^[a-zA-Z]+$', s))

    def __init__(self):
        self.root = None 
    def insert(self, word : str):
        if not self.validate(word): 
            print("Inserting multi word strings are not allowed")
            return 
        if self.root is None: 
            self.root = Node( True, False )
        currentNode = self.root 
        word = word.lower()
        for i in range(len(word)): 
            
            index = ord(word[i]) - 97
            
            if currentNode.children[index] == None :
                currentNode.children[index] = Node(False)
            currentNode = currentNode.children[index]
        currentNode.terminal = True 

    def getAll(self, current=None, prefix="", words = []):

        if current is None:
            current = self.root
            
        if current.terminal:
            print(prefix)
            words.append(prefix)

        for i in range(26):
            if current.children[i]:
                self.getAll(current.children[i], prefix + chr(i + 97))
           
        if current == self.root : 
            print(words)
    def searchPrefix(self, prefix = ""): 
            pass
                    
        
trie1 = Trie()
trie1.insert("chess")
trie1.insert("chemistry")

trie1.getAll()
