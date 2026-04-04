class _Node:
    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None
        

class LRUCache:
    """Cache using doubly linked list and hashmap"""
    def __init__(self, capacity=128):
        self.capacity = max(1, int(capacity))
        self.nodes = {}
        self.head = _Node()
        self.tail = _Node()
        self.head.next = self.tail
        self.tail.prev = self.head

    def _detach(self, node):
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _attach_to_tail(self, node):
        last = self.tail.prev
        last.next = node
        node.prev = last
        node.next = self.tail
        self.tail.prev = node

    def _move_to_recent(self, node):
        self._detach(node)
        self._attach_to_tail(node)

    def get(self, key):
        node = self.nodes.get(key)
        if node is None:
            return None
        self._move_to_recent(node)
        return node.value

    def put(self, key, value):
        node = self.nodes.get(key)
        if node is not None:
            node.value = value
            self._move_to_recent(node)
            return

        node = _Node(key, value)
        self.nodes[key] = node
        self._attach_to_tail(node)

        if len(self.nodes) > self.capacity:
            lru_node = self.head.next
            self._detach(lru_node)
            del self.nodes[lru_node.key]

    def __len__(self):
        return len(self.nodes)
