# PowerSearch

PowerSearch is a local full-stack research paper search system built around a custom in-memory search engine.

It combines a React frontend, a FastAPI backend, and a custom search layer using an inverted index, trie-based autocomplete, pagination, and LRU caching over a `50,000`-paper Semantic Scholar corpus. The project is designed to be both practical and explainable: fast enough to feel responsive in use, while still grounded in core software engineering and data-structure concepts.

## What It Does

- searches a large paper corpus with paginated results
- supports low-latency autocomplete while typing
- serves the system through a backend API
- exposes a browser-based frontend for end-to-end local usage
- logs both backend and frontend request timings for inspection
- benchmarks the custom engine against SQLite baselines

## System Overview

### Search Engine

The search engine is built in memory and uses:

- an inverted index for token-to-document lookup
- a trie for prefix-based autocomplete
- LRU caches for repeated search and autocomplete requests
- pagination for full search results

To reduce startup cost, the expensive search structures are serialized and loaded from disk when available. Runtime caches are not serialized; they start empty and warm naturally during use.

### Backend API

The backend is built with FastAPI and exposes:

- `GET /health`
- `POST /search`
- `GET /autocomplete`

The backend also logs request timings, which makes it easy to observe cache hits and compare API latency with browser-observed latency.

### Frontend

The frontend is built with React and provides:

- a search input
- live autocomplete suggestions
- paginated results
- browser console timing logs for autocomplete and search requests

Together, the frontend and backend make the project a true local end-to-end full-stack application rather than only a backend engine.

## Dataset

The current system runs on a Semantic Scholar dataset containing `50,000` records. Each record includes metadata such as title, abstract, year, citation information, and paper URL.

The engine indexes title and abstract text for search, and title tokens for trie-based autocomplete.

## API Usage

### Health Check

```bash
curl http://127.0.0.1:8000/health
```

### Search

```bash
curl -X POST http://127.0.0.1:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "deep learning",
    "offset": 0,
    "limit": 5
  }'
```

### Autocomplete

```bash
curl "http://127.0.0.1:8000/autocomplete?q=deep%20learning&k=5"
```

## Benchmarks

The project includes a reproducible SQLite benchmark comparing the custom engine against:

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

- this is a local SQLite baseline, not a universal comparison against all SQL systems
- `LIKE` is intentionally the naive baseline
- `FTS5` is the more meaningful full-text SQL comparison

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

Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

Start the backend:

```bash
backend/venv/bin/uvicorn main:app --app-dir backend/src --reload
```

The backend runs at:

```text
http://127.0.0.1:8000
```

### Frontend

Install dependencies:

```bash
cd frontend
npm install
```

Start the frontend:

```bash
npm run dev -- --host 127.0.0.1 --port 5173
```

The frontend runs at:

```text
http://127.0.0.1:5173
```

## Benchmark Setup

To rebuild and rerun the SQLite benchmark:

```bash
backend/venv/bin/python backend/src/db/benchmark/sqlite_benchmark.py
```

The generated SQLite benchmark database is kept local and ignored by Git.

## Current Scope

Implemented:

- local full-stack search flow
- backend API
- frontend integration
- autocomplete
- paginated search
- in-memory engine
- serialization for startup optimization
- LRU caching
- SQLite benchmark proof

Future improvements:

- cleaner package-style imports in the engine
- stronger deployment hardening
- richer ranking beyond recency-first ordering
- more advanced filtering and query controls

## Why This Project Is Interesting

PowerSearch sits at the intersection of:

- data structures
- backend engineering
- API design
- benchmarking
- frontend integration

It is not just a crawler, not just a UI, and not just a backend service. It is a measurable, explainable full-stack search system built around core software engineering ideas.
