from inverted_index import InvertedIndex
from trie import Trie 
import json 
import os
import re


def open_papers_json():
	"""Load and return data from backend/src/db/papers.json."""
	papers_path = os.path.join(os.path.dirname(__file__), "..", "db", "papers.json")
	with open(os.path.abspath(papers_path), "r", encoding="utf-8") as file:
		return json.load(file)


def initialize_objects():
	"""Initialize startup objects for search."""
	papers = open_papers_json()
	inverted_index = InvertedIndex(papers)
	trie = Trie()

	for paper in papers:
		paper_id = paper.get("id")
		for token in re.findall(r"[a-zA-Z]+", paper.get("title", "")):
			trie.insert(token, paper_id)

	return papers, inverted_index, trie


papers, invertedIndex  , prefix_tree = initialize_objects()


if __name__ == "__main__":
	print(f"Loaded papers.json with {len(papers)} records")
	print("Initialized InvertedIndex and Trie objects")
