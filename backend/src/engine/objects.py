from inverted_index import InvertedIndex
from trie import Trie
from lru import LRUCache
import json
import os
import pickle
import re

ENGINE_DIR = os.path.dirname(__file__)
DATASET_PATH = os.path.abspath(
    os.path.join(
        ENGINE_DIR,
        "..",
        "db",
        "semantic_scholar_papers.json",
    )
)
ARTIFACT_DIR = os.path.join(ENGINE_DIR, "artifacts")
ARTIFACT_PATH = os.path.join(ARTIFACT_DIR, "semantic_engine.pkl")


def open_semantic_json():
    """Load Semantic Scholar dataset."""
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
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


def build_engine_objects():
    """Build papers, inverted index, and trie from the raw dataset."""
    raw_papers = open_semantic_json()
    papers = [normalize_semantic_paper(p) for p in raw_papers]

    inverted_index = InvertedIndex(papers)
    trie = Trie()

    for paper in papers:
        paper_id = paper.get("id")
        for token in re.findall(r"[a-zA-Z]+", paper.get("title") or ""):
            trie.insert(token, paper_id)

    return papers, inverted_index, trie


def save_engine_objects(papers, inverted_index, trie):
    """Persist the expensive search objects so startup can load them quickly later."""
    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    payload = {
        "papers": papers,
        "inverted_index": inverted_index,
        "prefix_tree": trie,
    }
    temp_path = ARTIFACT_PATH + ".tmp"
    with open(temp_path, "wb") as file:
        pickle.dump(payload, file, protocol=pickle.HIGHEST_PROTOCOL)
    os.replace(temp_path, ARTIFACT_PATH)


def load_engine_objects():
    """Load previously serialized search objects."""
    with open(ARTIFACT_PATH, "rb") as file:
        payload = pickle.load(file)
    return payload["papers"], payload["inverted_index"], payload["prefix_tree"]


def artifact_is_fresh():
    if not os.path.exists(ARTIFACT_PATH):
        return False
    return os.path.getmtime(ARTIFACT_PATH) >= os.path.getmtime(DATASET_PATH)


def initialize_objects():
    """Load serialized objects when available, otherwise build and save them."""
    if artifact_is_fresh():
        papers, inverted_index, trie = load_engine_objects()
        source = "artifact"
    else:
        papers, inverted_index, trie = build_engine_objects()
        save_engine_objects(papers, inverted_index, trie)
        source = "dataset"

    search_cache = LRUCache(128)
    autocomplete_cache = LRUCache(1024)
    return papers, inverted_index, trie, search_cache, autocomplete_cache, source


papers, invertedIndex, prefix_tree, search_cache, autocomplete_cache, OBJECTS_SOURCE = initialize_objects()


if __name__ == "__main__":
    print(f"Loaded semantic_scholar_papers.json with {len(papers)} records")
    print(f"Initialized InvertedIndex and Trie from {OBJECTS_SOURCE}")
    print("Initialized fresh LRU cache objects")
