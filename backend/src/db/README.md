# Dataset Notes

This folder contains two paper datasets with different record structures and slightly different best-use cases.

Current counts in this repo:
- `papers.json` (OpenAlex): `5,000` records
- `semantic_scholar_papers.json` (Semantic Scholar): `50,000` records

## `papers.json` (OpenAlex)

Source:
- Fetched by [`getdata.py`](/home/kavin/projects/PowerSearch/backend/src/db/getdata.py)

Current record shape:
- `id`: OpenAlex work URL, for example `https://openalex.org/W2194775991`
- `title`
- `publication_year`
- `cited_by_count`
- `referenced_works`: list of OpenAlex work URLs
- `abstract_inverted_index`: token-position map instead of a plain abstract string

Best usage:
- Good for citation-style metadata and OpenAlex-native identifiers
- Good when you want referenced work links already in OpenAlex URL form
- Less convenient for direct text search because the abstract is stored as an inverted index and usually needs reconstruction before indexing or display
- This is the dataset currently used by the engine implementation in `backend/src/engine`

Notes:
- The schema is close to the raw OpenAlex response
- If you need a readable abstract, convert `abstract_inverted_index` into plain text first

## `semantic_scholar_papers.json` (Semantic Scholar)

Source:
- Fetched by [`fetch_semantic_scholar.py`](/home/kavin/projects/PowerSearch/backend/src/db/fetch_semantic_scholar.py)

Current record shape:
- `paper_id`: Semantic Scholar paper id
- `paper_url`: Semantic Scholar paper URL
- `title`
- `abstract`
- `fields`: list of fields of study
- `year`
- `citation_count`
- `influential_citations`
- `references`: list of referenced Semantic Scholar paper ids
- `text_for_indexing`: `title + abstract` combined into one plain-text field

Best usage:
- Better for semantic search, vector indexing, and direct keyword search
- Better when you want a ready-to-use text field without reconstructing the abstract
- Better when you want a stable UI link to the paper through `paper_url`
- Intended for the next stage of engine migration, but not yet the active engine backing store

Notes:
- The schema is normalized and easier to consume in an application layer
- `references` are paper ids, not full URLs
- Some records may still have missing `abstract` or empty `fields`

## Quick Comparison

Use `papers.json` when:
- You want OpenAlex ids and referenced work URLs
- You are working with OpenAlex metadata directly
- You want compatibility with the current engine code

Use `semantic_scholar_papers.json` when:
- You want easier indexing and retrieval
- You want plain-text searchable content
- You want direct paper links through `paper_url`
- You are preparing for the Semantic Scholar-based engine version

In short:
- OpenAlex dataset: richer raw scholarly metadata format
- Semantic Scholar dataset: cleaner app-ready retrieval format with more records in this repo
