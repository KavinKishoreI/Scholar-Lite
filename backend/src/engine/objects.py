from inverted_index import InvertedIndex
from trie import Trie
import json
import os
import re


def open_semantic_json():
    """Load Semantic Scholar dataset."""
    papers_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "db",
        "semantic_scholar_papers.json",
    )
    with open(os.path.abspath(papers_path), "r", encoding="utf-8") as file:
        return json.load(file)


def normalize_semantic_paper(p):
    """Map Semantic Scholar fields to engine-friendly keys."""
    return {
        "id": p.get("paper_id"),
        "title": p.get("title"),
        "year": p.get("year"),
        # Align with existing ranking key expected by MinHeap.
        "cited_by_count": p.get("citation_count", 0),
        # Keep original fields in case callers need them.
        "paper_url": p.get("paper_url"),
        "abstract": p.get("abstract"),
        "fields": p.get("fields") or [],
        "references": p.get("references") or [],
        "text_for_indexing": p.get("text_for_indexing"),
    }


def initialize_objects():
    """Initialize startup objects for search."""
    raw_papers = open_semantic_json()
    papers = [normalize_semantic_paper(p) for p in raw_papers]

    inverted_index = InvertedIndex(papers)
    trie = Trie()

    for paper in papers:
        paper_id = paper.get("id")
        for token in re.findall(r"[a-zA-Z]+", paper.get("title") or ""):
            trie.insert(token, paper_id)

    return papers, inverted_index, trie


papers, invertedIndex, prefix_tree = initialize_objects()


if __name__ == "__main__":
    print(f"Loaded semantic_scholar_papers.json with {len(papers)} records")
    print("Initialized InvertedIndex and Trie objects")
