# SQLite Benchmark

This folder contains a reproducible benchmark comparing the project search engine against two SQLite baselines on the same `50,000`-paper Semantic Scholar dataset.

## What Is Compared

- `naive_like`
  - A plain SQLite table query using `LOWER(text_blob) LIKE '%token%'`
- `fts_indexed`
  - A SQLite `FTS5` full-text index with AND-style token matching
- `engine`
  - The in-memory search engine implemented with:
    - inverted index
    - trie-based autocomplete support
    - paginated ranking through the custom engine pipeline

## Files

- `sqlite_benchmark.py`
  - Rebuilds the benchmark SQLite database and runs the benchmark queries
- `semantic_scholar_benchmark.db`
  - Generated benchmark database created by the script

## Command

Run the benchmark with:

```bash
backend/venv/bin/python backend/src/db/benchmark/sqlite_benchmark.py
```

## Dataset Used

- Source file: `backend/src/db/semantic_scholar_papers.json`
- Records inserted into SQLite: `50,000`

## Latest Results

Results from the latest local run:

### Query: `deep learning`

- `naive_like`
  - total: `7973`
  - time: `0.166910s`
- `fts_indexed`
  - total: `7732`
  - time: `0.041644s`
- `engine`
  - total: `7732`
  - time: `0.010361s`

### Query: `machine learning`

- `naive_like`
  - total: `14901`
  - time: `0.169136s`
- `fts_indexed`
  - total: `14622`
  - time: `0.071798s`
- `engine`
  - total: `14622`
  - time: `0.018114s`

### Query: `graph neural`

- `naive_like`
  - total: `1830`
  - time: `0.154679s`
- `fts_indexed`
  - total: `1400`
  - time: `0.007901s`
- `engine`
  - total: `1401`
  - time: `0.002075s`

## Notes

- `naive_like` is not semantically identical to the engine because substring matching can overcount results.
- `fts_indexed` is the fairer SQL comparison because it behaves more like token-based full-text search.
- The engine and SQLite FTS counts are very close, with a small tokenizer-related mismatch on `graph neural`.
- The benchmark database is generated locally and is ignored by Git via `.gitignore`.
