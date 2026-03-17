from inverted_index import InvertedIndex
class MinHeap: 
    """ Maintains a minheap of k length """
    def __init__(self, k: int):
        self.minHeap = [None] 
        self.max_size = k 
        self.size = 0 
    def extract_min(self) : 
        if self.size == 0 : 
            return 
        else : 
            min_element = self.minHeap[1]
            
            self.minHeap[1] = self.minHeap[self.size]
            self.minHeap.pop()
            self.size -= 1 
            i = 1
            while 2*i <= self.size: 
                minimum = i 
                if 2*i <= self.size and self.minHeap[2* i]["cited_by_count"] < self.minHeap[minimum]["cited_by_count"] :
                    minimum = 2 * i
                if 2*i +1 <= self.size and  self.minHeap[2 * i+ 1 ]['cited_by_count'] < self.minHeap[minimum]['cited_by_count'] :
                    minimum  = 2 * i + 1 
                if i == minimum : 
                    break 
                else : 
                    self.minHeap[minimum] , self.minHeap[i] = self.minHeap[i], self.minHeap[minimum]
                    i = minimum
            return min_element

    def insert(self, element):
        """Insert while keeping only top-k largest cited_by_count elements."""
        if self.max_size <= 0:
            return

        # If heap has room, push and heapify up.
        if self.size < self.max_size:
            self.minHeap.append(element)
            self.size += 1
            i = self.size
            while i > 1:
                parent = i // 2
                if self.minHeap[i]["cited_by_count"] < self.minHeap[parent]["cited_by_count"]:
                    self.minHeap[i], self.minHeap[parent] = self.minHeap[parent], self.minHeap[i]
                    i = parent
                else:
                    break
            return

        # Heap is full: only keep the new element if it is larger than current minimum.
        if element["cited_by_count"] <= self.minHeap[1]["cited_by_count"]:
            return

        self.minHeap[1] = element
        i = 1
        while 2 * i <= self.size:
            minimum = i
            left = 2 * i
            right = 2 * i + 1

            if (
                left <= self.size
                and self.minHeap[left]["cited_by_count"] < self.minHeap[minimum]["cited_by_count"]
            ):
                minimum = left

            if (
                right <= self.size
                and self.minHeap[right]["cited_by_count"] < self.minHeap[minimum]["cited_by_count"]
            ):
                minimum = right

            if minimum == i:
                break

            self.minHeap[minimum], self.minHeap[i] = self.minHeap[i], self.minHeap[minimum]
            i = minimum
    def getTopK(self):
        if self.size == 0:
            print ("Elements not inserted ") 
            return []
        else : 
            return sorted(self.minHeap[1:self.size + 1], key=lambda x: x["cited_by_count"], reverse=True)
            

