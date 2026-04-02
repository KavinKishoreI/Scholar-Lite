# Engine Data Structure Report

## Current Scope

The current engine is designed to work with the OpenAlex dataset in [`papers.json`](/home/kavin/projects/PowerSearch/backend/src/db/papers.json), not the Semantic Scholar dataset.

Verified behavior from terminal testing:
- engine loads `5,000` OpenAlex papers
- `query_router.py` runs successfully end-to-end
- example queries such as `"deep"`, `"machine learning"`, and `"graph"` return ranked results
- stopword-only and empty queries now return no results instead of noisy matches

## Main Data Structures

### 1. Inverted Index

Implementation:
- [`inverted_index.py`](/home/kavin/projects/PowerSearch/backend/src/engine/inverted_index.py)

Structure:
- `self.index`: `dict[word] -> set[paper_id]`
- `self.map`: `dict[paper_id] -> full paper record`

How it is used:
- During startup, each paper title is tokenized and inserted into the inverted index
- Search terms are looked up directly in `self.index`
- Matching paper ids are then resolved back to full documents through `self.map`

Why this structure fits:
- Exact-word lookup is fast
- Set intersection is a natural way to support multi-word AND-style retrieval
- Keeping a separate `paper_id -> record` map avoids rescanning the full paper list after search

Current limitation:
- Only title tokens are indexed
- Abstracts, referenced works, and other metadata are not indexed yet

### 2. Trie

Implementation:
- [`trie.py`](/home/kavin/projects/PowerSearch/backend/src/engine/trie.py)

Structure:
- Each node stores:
  - `children`: fixed array of length 26
  - `terminal`: whether the path ends a word
  - `paper_ids`: set of paper ids for completed words

How it is used:
- Title tokens are inserted into the trie at startup
- The router uses it for prefix expansion on the last query token
- This supports autocomplete-like behavior such as matching `"deep"` and prefix continuations

Why this structure fits:
- Prefix lookup is efficient
- It complements the inverted index well: exact-word lookup comes from the inverted index, prefix expansion comes from the trie

Current limitation:
- It only accepts alphabetic tokens
- It uses a dense 26-slot child array, which is simple but not memory-optimal

### 3. Min-Heap

Implementation:
- [`minheap.py`](/home/kavin/projects/PowerSearch/backend/src/engine/minheap.py)

Structure:
- 1-indexed array-backed min-heap
- Stores at most `k` paper records
- Heap order is based on OpenAlex `cited_by_count`

How it is used:
- After search collects candidate paper ids, the router inserts matching papers into a bounded min-heap
- The heap keeps only the top-`k` most-cited papers
- Final output is returned in descending citation order

Why this structure fits:
- Efficient top-`k` selection without sorting every candidate
- Good match for “best few results” style autocomplete/search output

Current limitation:
- Ranking is based only on citation count
- It does not currently combine relevance score and citation score

### 4. Router-Level Composition

Implementation:
- [`query_router.py`](/home/kavin/projects/PowerSearch/backend/src/engine/query_router.py)
- [`objects.py`](/home/kavin/projects/PowerSearch/backend/src/engine/objects.py)

Structure:
- `objects.py` builds and exposes shared startup objects:
  - paper list
  - inverted index
  - trie
- `QueryRouter` composes these structures to execute search

How it works:
1. Load `papers.json`
2. Build inverted index from title tokens
3. Build trie from title tokens
4. Tokenize the query
5. Intersect exact matches across all query tokens
6. Use trie prefix search on the last token
7. Rank candidate papers with the min-heap

Why this structure fits:
- Simple search pipeline
- Good separation between indexing, prefix expansion, and ranking
- Fast enough for small-to-medium in-memory datasets

## Current Logical State

The earlier logical issues in the OpenAlex engine path were fixed:
- token lookup in the inverted index now uses the full normalized token
- query tokenization is handled consistently
- empty queries are handled safely
- stopword-only queries no longer return misleading results
- inverted index lookup returns a copy of the stored set, so search-time intersections do not mutate shared index state

This means the engine is now working logically for its current OpenAlex target.

## Remaining Design Constraints

- The engine is still OpenAlex-specific:
  - ids assume `id`
  - ranking assumes `cited_by_count`
  - startup loading assumes [`papers.json`](/home/kavin/projects/PowerSearch/backend/src/db/papers.json)
- It does not yet use the Semantic Scholar schema:
  - `paper_id`
  - `paper_url`
  - `citation_count`
  - `text_for_indexing`
- There is no active cache layer yet:
  - [`lru.py`](/home/kavin/projects/PowerSearch/backend/src/engine/lru.py) is still empty

## Practical Summary

Right now, the engine is a compact in-memory search system built from:
- a hash-based inverted index for exact term lookup
- a trie for prefix matching
- a bounded min-heap for top-`k` ranking

That combination is appropriate for the current OpenAlex-backed implementation and is now functioning correctly in terminal tests. The next architectural step would be adapting the same search pipeline, or a revised version of it, to the Semantic Scholar dataset.
