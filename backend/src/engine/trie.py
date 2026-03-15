from typing import List
import re 
class Node : 
    def __init__(self, root: bool= False, terminal : bool = False):
        self.children: List[Node] = [None] * 26
        self.root = root
        self.terminal = terminal
        if self.terminal: 
            self.paper_ids = set()
        else : 
            self.paper_ids = None
class Trie:
    def validate(self,s): 
        """Validate and discard entries with numbers and spaces"""
        return bool(re.match(r'^[a-zA-Z]+$', s))

    def __init__(self):
        self.root = None 
    def insert(self, word : str, paper_id : str):
        """ Insert a word from a paper and store a paper_id"""
        if not self.validate(word): 
            raise ValueError("Insertion of multi word strings and special characters are not allowed")
            return 
        if self.root is None: 
            self.root = Node( True, False )
        currentNode = self.root 
        word = word.lower()
        for i in range(len(word)): 
            
            index = ord(word[i]) - 97
            
            if currentNode.children[index] is  None :
                currentNode.children[index] = Node(False)
            currentNode = currentNode.children[index]
        currentNode.terminal = True 
        if currentNode.paper_ids is None: 
            currentNode.paper_ids = set() 
        currentNode.paper_ids.add(paper_id) 

    def getAll(self, current=None, result=None):
        """Return set of all paperids """
        if result is None:
            result = set()
        if current is None:
            current = self.root

        if current.terminal:
            result.update(current.paper_ids)

        for i in range(26):
            if current.children[i]:
                self.getAll(current.children[i], result)

        return result
    def searchPrefix(self, prefix = ""): 
        """Returns a set of all paperids for corresponding prefix"""
        if len(prefix) < 2 or not self.validate(prefix) :
            print("prefix length not sufficient")
            return set()
        else : 
            prefix = prefix.lower()
            currentNode = self.root
            if currentNode is None : 
                    return set()
            
            else: 
                found = True 
                for i in range(len(prefix)): 
                    index = ord(prefix[i]) - 97 
                    if currentNode.children[index]: 
                        currentNode = currentNode.children[index]
                    else: 
                        found = False 
                        break
                if found: 
                    return self.getAll(currentNode)
                else: 
                    return set()
if __name__ == '__main__':
    trie1 = Trie()
    trie1.insert("chess", '122')
    trie1.insert('doms', '134')
    trie1.insert('DoctoR', "200")
    trie1.insert("CHe", '134')
    trie1.insert("champ", '160')
    trie1.insert('docTor', '22')
    trie1.insert('dosage', '134')
    trie1.insert('camp', '140')
    print(trie1.getAll())
    print(trie1.searchPrefix("doc"))