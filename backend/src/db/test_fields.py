"""
Test which Semantic Scholar API fields work
"""
import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load from explicit path
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("SEMANTIC_API_KEY")

# Test different field combinations
field_sets = [
    ("basic", "paperId,title"),
    ("with_counts", "paperId,title,citationCount,influentialCitationCount"),
    ("with_year", "paperId,title,citationCount,publicationYear"),
    ("with_abstract", "paperId,title,abstract,citationCount"),
    ("with_authors", "paperId,title,citationCount,authors"),
    ("with_fields", "paperId,title,citationCount,fieldsOfStudy"),
    ("all_simple", "paperId,title,abstract,citationCount,publicationYear,authors,fieldsOfStudy"),
]

headers = {"x-api-key": api_key}
base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

print("Testing field combinations:\n")
for name, fields in field_sets:
    try:
        params = {"query": "machine learning", "limit": 1, "fields": fields}
        r = requests.get(base_url, headers=headers, params=params, timeout=10)
        status = "✓" if r.status_code == 200 else "✗"
        print(f"{status} {name:<20} ({len(fields)} chars) -> {r.status_code}")
        if r.status_code == 200:
            data = r.json().get("data", [])
            if data:
                paper = data[0]
                available_fields = [k for k in paper.keys() if paper[k] is not None]
                print(f"  Available: {', '.join(available_fields)}")
    except Exception as e:
        print(f"✗ {name:<20} -> Error: {e}")
