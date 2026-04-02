"""
Quick diagnostics for Semantic Scholar API
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("SEMANTIC_API_KEY")

if not api_key:
    print("✗ SEMANTIC_API_KEY not found in .env")
    exit(1)

print(f"API Key: {api_key[:20]}...")
print("\nTesting Semantic Scholar API endpoints...\n")

# Test 1: Check if API key is in header
print("1. Testing with x-api-key header...")
url = "https://api.semanticscholar.org/graph/v1/paper/search"
headers = {"x-api-key": api_key}
params = {
    "query": "machine learning",
    "limit": 1,
    "fields": "paperId,title,citationCount"
}

try:
    r = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print("   ✓ Success!")
        data = r.json()
        print(f"   Response keys: {data.keys()}")
        if "data" in data:
            print(f"   Found {len(data.get('data', []))} papers")
    else:
        print(f"   Response: {r.text[:300]}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
