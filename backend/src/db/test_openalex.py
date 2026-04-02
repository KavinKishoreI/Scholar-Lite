"""
Test OpenAlex API with 'search' and 'abstract' fields
"""
import requests
import os
from dotenv import load_dotenv
from pathlib import Path

# Load from explicit path
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(env_path)

# Test OpenAlex with search and abstract
url = "https://api.openalex.org/works"
params = {
    "search": "machine learning",
    "select": "id,title,abstract",
    "per-page": 1,
    "mailto": "kavinpersonal.id06@gmail.com"
}

print("Testing OpenAlex with 'search' and 'abstract' fields...")
try:
    response = requests.get(url, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        if results:
            paper = results[0]
            print("✓ Success! Found paper:")
            print(f"  Title: {paper.get('title')}")
            print(f"  Abstract: {paper.get('abstract') is not None}")
        else:
            print("✗ No results found")
    else:
        print(f"Error: {response.text[:300]}")
except Exception as e:
    print(f"Error: {e}")
