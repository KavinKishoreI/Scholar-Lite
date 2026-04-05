# PowerSearch

PowerSearch is a local full-stack research paper search system built around a custom in-memory search engine.

It combines:
- a React frontend for live search and autocomplete
- a FastAPI backend for search APIs
- a custom engine using an inverted index, trie-based prefix search, pagination, and LRU caching
- a `50,000`-paper Semantic Scholar dataset focused on computer science and adjacent technical topics

The goal of the project is simple: build a search system that feels responsive in practice, is explainable from a data-structures point of view, and can be benchmarked against SQL-based baselines.

## Highlights

- Built over `50,000` Semantic Scholar records
- Custom in-memory search engine using:
  - inverted index
  - trie for autocomplete
  - LRU caching for search and autocomplete
- FastAPI backend with:
  - `POST /search`
  - `GET /autocomplete`
  - `GET /health`
- React frontend with:
  - live autocomplete
  - paginated search results
  - client-side latency logging
- Serialized engine objects for faster startup
- SQLite benchmark suite comparing:
  - naive `LIKE`
  - indexed `FTS5`
  - custom engine

## Architecture

### Backend

The backend lives in `backend/src`.

- [main.py](/home/kavin/projects/PowerSearch/backend/src/main.py)
  - FastAPI application
  - logs request timings for search and autocomplete
- [query_router.py](/home/kavin/projects/PowerSearch/backend/src/engine/query_router.py)
  - routes queries through the engine
  - handles strict AND search, pagination, autocomplete, and cache lookups
- [inverted_index.py](/home/kavin/projects/PowerSearch/backend/src/engine/inverted_index.py)
  - token-to-document lookup
- [trie.py](/home/kavin/projects/PowerSearch/backend/src/engine/trie.py)
  - prefix-based autocomplete
- [lru.py](/home/kavin/projects/PowerSearch/backend/src/engine/lru.py)
  - manual LRU cache implementation using a hashmap and doubly linked list
- [objects.py](/home/kavin/projects/PowerSearch/backend/src/engine/objects.py)
  - loads serialized engine artifacts when available
  - otherwise builds the engine from the Semantic Scholar dataset and saves the artifact

### Frontend

The frontend lives in `frontend/`.

- [App.jsx](/home/kavin/projects/PowerSearch/frontend/src/App.jsx)
  - search UI
  - autocomplete UI
  - paginated result rendering
  - browser-side latency logging
- [styles.css](/home/kavin/projects/PowerSearch/frontend/src/styles.css)
  - visual styling

## Dataset

The engine currently runs on the Semantic Scholar dataset stored in:

- [semantic_scholar_papers.json](/home/kavin/projects/PowerSearch/backend/src/db/semantic_scholar_papers.json)

The dataset currently contains:
- `50,000` records
- paper identifiers
- titles
- years
- abstracts
- paper URLs
- citation counts

The engine indexes title and abstract text for search, and title tokens for trie-based autocomplete.

## API

### `GET /health`

Simple health check.

Example:

```bash
curl http://127.0.0.1:8000/health
```

### `POST /search`

Paginated search endpoint.

Example:

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "deep learning",
    "offset": 0,
    "limit": 5
  }'
```

### `GET /autocomplete`

Autocomplete endpoint.

Example:

```bash
curl "http://127.0.0.1:8000/autocomplete?q=deep%20learning&k=5"
```

## Benchmarks

This project includes a reproducible SQLite benchmark under:

- [benchmark/README.md](/home/kavin/projects/PowerSearch/backend/src/db/benchmark/README.md)
- [sqlite_benchmark.py](/home/kavin/projects/PowerSearch/backend/src/db/benchmark/sqlite_benchmark.py)

It compares the custom engine against:
- naive SQLite `LIKE` search
- indexed SQLite `FTS5`

Latest local benchmark results:

### `deep learning`

- naive SQLite `LIKE`: `0.166910s`
- SQLite `FTS5`: `0.041644s`
- custom engine: `0.010361s`

### `machine learning`

- naive SQLite `LIKE`: `0.169136s`
- SQLite `FTS5`: `0.071798s`
- custom engine: `0.018114s`

### `graph neural`

- naive SQLite `LIKE`: `0.154679s`
- SQLite `FTS5`: `0.007901s`
- custom engine: `0.002075s`

Important note:
- the SQLite benchmark is a local baseline, not a universal claim against all SQL servers
- `LIKE` is intentionally the naive baseline
- `FTS5` is the fairer full-text SQL comparison

## Local Performance Notes

In local testing:
- repeated backend cached requests dropped to near-microsecond processing times in server logs
- browser-observed repeated requests were generally in the `5–10 ms` range

That difference is expected because browser timings include:
- request/response overhead
- JSON parsing
- frontend runtime overhead

## Setup

### Backend

Create and activate your virtual environment if needed, then install backend dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Run the API:

```bash
backend/venv/bin/uvicorn main:app --app-dir backend/src --reload
```

Backend runs at:

```text
http://127.0.0.1:8000
```

### Frontend

Install frontend dependencies:

```bash
cd frontend
npm install
```

Start the React dev server:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

Frontend runs at:

```text
http://127.0.0.1:5173
```

## Benchmark Setup

To rebuild and rerun the SQLite benchmark:

```bash
backend/venv/bin/python backend/src/db/benchmark/sqlite_benchmark.py
```

This generates:

- [semantic_scholar_benchmark.db](/home/kavin/projects/PowerSearch/backend/src/db/benchmark/semantic_scholar_benchmark.db)

That `.db` file is ignored by Git.

## Notes On Serialization

The engine serializes the expensive core search objects:
- normalized papers
- inverted index
- trie

These are stored under:

- [artifacts](/home/kavin/projects/PowerSearch/backend/src/engine/artifacts)

Runtime caches are not serialized:
- `search_cache`
- `autocomplete_cache`

They start empty on boot and warm naturally during usage.

## Current Scope

What is already implemented:
- local full-stack search flow
- backend API
- frontend integration
- autocomplete
- paginated search
- in-memory engine
- caching
- SQLite benchmark proof

What is still open for future improvement:
- cleaner package-style imports in the engine
- deployment hardening
- improved ranking beyond recency-first
- more advanced filtering
- production-grade startup optimization and artifact management

## Why This Project Is Interesting

PowerSearch is useful because it sits at the intersection of:
- data structures
- backend systems
- API design
- local benchmarking
- frontend integration

It is not just a crawler or just a UI. It is a measurable, explainable search system with a real full-stack workflow.
