import argparse
import json
import os
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import requests
from dotenv import load_dotenv
from requests import RequestException


SCRIPT_DIR = Path(__file__).resolve().parent
ENV_FILE = SCRIPT_DIR.parent.parent / ".env"
OUTPUT_FILE = SCRIPT_DIR / "semantic_scholar_papers.json"
STATE_FILE = SCRIPT_DIR / "semantic_scholar_state.json"
SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
BULK_SEARCH_URL = "https://api.semanticscholar.org/graph/v1/paper/search/bulk"
REQUEST_TIMEOUT = (10, 60)
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 2
SEARCH_RESULT_CAP = 999

DEFAULT_SHARD_QUERIES = [
    "machine learning",
    "deep learning",
    "reinforcement learning",
    "supervised learning",
    "unsupervised learning",
    "self supervised learning",
    "semi supervised learning",
    "transfer learning",
    "meta learning",
    "online learning",
    "active learning",
    "federated learning",
    "representation learning",
    "metric learning",
    "multimodal learning",
    "continual learning",
    "curriculum learning",
    "few shot learning",
    "zero shot learning",
    "graph neural networks",
    "graph machine learning",
    "computer vision",
    "natural language processing",
    "nlp",
    "computer vision deep learning",
    "machine learning for computer vision",
    "machine learning for natural language processing",
    "time series forecasting",
    "anomaly detection",
    "recommendation systems",
    "information retrieval",
    "speech recognition",
    "question answering",
    "generative models",
    "large language models",
    "transformer models",
    "convolutional neural networks",
    "recurrent neural networks",
    "classification machine learning",
    "regression machine learning",
    "clustering machine learning",
    "dimensionality reduction",
    "feature selection",
    "hyperparameter optimization",
    "bayesian optimization",
    "support vector machines",
    "decision trees",
    "random forests",
    "gradient boosting",
    "xgboost machine learning",
    "logistic regression machine learning",
    "linear regression machine learning",
    "probabilistic machine learning",
    "causal machine learning",
    "explainable ai",
    "interpretable machine learning",
    "fairness in machine learning",
    "robust machine learning",
    "adversarial machine learning",
    "privacy preserving machine learning",
    "medical image analysis",
    "bioinformatics machine learning",
    "drug discovery machine learning",
    "healthcare machine learning",
    "finance machine learning",
    "remote sensing machine learning",
    "robotics machine learning",
    "autonomous driving machine learning",
    "industrial machine learning",
    "predictive maintenance machine learning",
    "recommender systems deep learning",
    "language modeling",
    "document classification",
    "image segmentation",
    "object detection",
    "semantic segmentation",
    "knowledge graph learning",
    "retrieval augmented generation",
    "scientific machine learning",
    "physics informed machine learning",
    "survival analysis machine learning",
    "graph representation learning",
    "neural architecture search",
    "model compression machine learning",
    "time series classification",
    "algorithms",
    "data structures",
    "advanced data structures",
    "algorithms and data structures",
    "distributed systems",
    "database systems",
    "operating systems",
    "computer networks",
    "software engineering",
    "programming languages",
    "compiler optimization",
    "computer graphics",
    "human computer interaction",
    "cybersecurity",
    "cryptography",
    "formal methods",
    "program analysis",
    "quantum computing",
    "cloud computing",
    "edge computing",
    "parallel computing",
    "high performance computing",
    "knowledge representation",
    "knowledge graphs",
]

FIELDS = ",".join(
    [
        "paperId",
        "title",
        "abstract",
        "citationCount",
        "influentialCitationCount",
        "fieldsOfStudy",
        "year",
        "references.paperId",
    ]
)

load_dotenv(ENV_FILE)
API_KEY = os.getenv("SEMANTIC_API_KEY")


def build_paper_url(paper_id):
    if not paper_id:
        return None

    return f"https://www.semanticscholar.org/paper/{paper_id}"


def fetch_papers(query, offset=0, limit=100):
    if not API_KEY:
        raise RuntimeError(f"SEMANTIC_API_KEY not found in {ENV_FILE}")

    params = {
        "query": query,
        "offset": offset,
        "limit": limit,
        "fields": FIELDS,
    }

    headers = {"x-api-key": API_KEY}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                SEARCH_URL,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except RequestException as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(f"Semantic Scholar request failed: {exc}") from exc

            wait_seconds = RETRY_BACKOFF_SECONDS * attempt
            print(
                f"Request failed at offset {offset} on attempt {attempt}/{MAX_RETRIES}: {exc}. "
                f"Retrying in {wait_seconds} seconds..."
            )
            time.sleep(wait_seconds)


def fetch_papers_bulk(query, token=None, sort="paperId:asc"):
    if not API_KEY:
        raise RuntimeError(f"SEMANTIC_API_KEY not found in {ENV_FILE}")

    params = {
        "query": query,
        "fields": FIELDS,
        "sort": sort,
    }
    if token:
        params["token"] = token

    headers = {"x-api-key": API_KEY}

    try:
        response = requests.get(
            BULK_SEARCH_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except RequestException as exc:
        raise RuntimeError(f"Semantic Scholar bulk request failed: {exc}") from exc

    return response.json()


def process_paper(paper):
    references = paper.get("references") or []
    paper_id = paper.get("paperId")

    return {
        "paper_id": paper_id,
        "paper_url": build_paper_url(paper_id),
        "title": paper.get("title", ""),
        "abstract": paper.get("abstract", ""),
        "fields": paper.get("fieldsOfStudy") or [],
        "year": paper.get("year"),
        "citation_count": paper.get("citationCount", 0),
        "influential_citations": paper.get("influentialCitationCount", 0),
        "references": [
            reference.get("paperId")
            for reference in references
            if reference.get("paperId")
        ],
        "text_for_indexing": f"{paper.get('title', '')} {paper.get('abstract', '')}".strip(),
    }


def build_shard_queries(base_query):
    base_query = base_query.strip()
    queries = []
    seen = set()

    for query in [base_query, *DEFAULT_SHARD_QUERIES]:
        normalized = " ".join(query.split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            queries.append(normalized)

    return queries


def load_existing_records(output_file):
    if not output_file.exists():
        return [], set()

    try:
        records = json.loads(output_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse existing JSON file {output_file}: {exc}") from exc

    if not isinstance(records, list):
        raise RuntimeError(f"Expected a JSON array in {output_file}")

    seen_ids = set()
    deduped_records = []
    for record in records:
        if not isinstance(record, dict):
            continue

        paper_id = record.get("paper_id")
        dedupe_key = paper_id or f"{record.get('title', '')}|{record.get('year')}"
        if dedupe_key in seen_ids:
            continue

        seen_ids.add(dedupe_key)
        deduped_records.append(record)

    return deduped_records, seen_ids


def load_state(state_file, shard_queries):
    if not state_file.exists():
        return {"next_shard_index": 0, "next_offset": 0}

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"next_shard_index": 0, "next_offset": 0}

    next_shard_index = int(state.get("next_shard_index", 0))
    next_offset = int(state.get("next_offset", 0))

    if next_shard_index < 0 or next_shard_index >= len(shard_queries):
        next_shard_index = 0
    if next_offset < 0 or next_offset >= SEARCH_RESULT_CAP:
        next_offset = 0

    return {"next_shard_index": next_shard_index, "next_offset": next_offset}


def save_state(state, state_file=STATE_FILE):
    write_json_atomic(state, state_file)


def collect_query_results(
    query,
    seen_ids,
    max_new_records,
    batch_size=100,
    delay_seconds=1.0,
    start_offset=0,
):
    if max_new_records <= 0:
        return [], 0, False

    offset = start_offset
    collected = []

    while offset < SEARCH_RESULT_CAP and len(collected) < max_new_records:
        remaining_cap = SEARCH_RESULT_CAP - offset
        remaining_needed = max_new_records - len(collected)
        current_limit = min(batch_size, remaining_cap, remaining_needed)

        if current_limit <= 0 or offset + current_limit >= 1000:
            break

        data = fetch_papers(query, offset=offset, limit=current_limit)
        batch = data.get("data", [])

        if not batch:
            break

        added_this_batch = 0
        for paper in batch:
            processed = process_paper(paper)
            paper_id = processed.get("paper_id")
            dedupe_key = paper_id or f"{processed.get('title', '')}|{processed.get('year')}"
            if dedupe_key in seen_ids:
                continue

            seen_ids.add(dedupe_key)
            collected.append(processed)
            added_this_batch += 1

            if len(collected) >= max_new_records:
                break

        print(
            f"Query '{query}' offset {offset}: added {added_this_batch} new papers "
            f"({len(collected)} new from this query)"
        )

        if len(batch) < current_limit:
            return collected, 0, True

        offset += current_limit
        if offset >= SEARCH_RESULT_CAP or len(collected) >= max_new_records:
            break

        time.sleep(delay_seconds)

    shard_exhausted = offset >= SEARCH_RESULT_CAP
    next_offset = 0 if shard_exhausted else offset
    return collected, next_offset, shard_exhausted


def crawl(
    query,
    max_papers=1000,
    batch_size=100,
    delay_seconds=1.0,
    checkpoint_every=10,
    output_file=OUTPUT_FILE,
):
    offset = 0
    collected = []
    batches_fetched = 0

    while len(collected) < max_papers:
        current_limit = min(batch_size, max_papers - len(collected))
        data = fetch_papers(query, offset=offset, limit=current_limit)
        batch = data.get("data", [])

        if not batch:
            break

        collected.extend(process_paper(paper) for paper in batch)
        batches_fetched += 1
        print(f"Collected {len(collected)} papers")

        if checkpoint_every and batches_fetched % checkpoint_every == 0:
            save_records(collected, output_file=output_file)
            print(f"Checkpoint saved with {len(collected)} records")

        if len(batch) < current_limit:
            break

        offset += current_limit
        time.sleep(delay_seconds)

    return collected


def crawl_sharded(
    base_query,
    max_papers=50000,
    batch_size=100,
    delay_seconds=1.0,
    checkpoint_every=5,
    output_file=OUTPUT_FILE,
    state_file=STATE_FILE,
):
    shard_queries = build_shard_queries(base_query)
    collected, seen_ids = load_existing_records(output_file)
    state = load_state(state_file, shard_queries)
    starting_total = len(collected)
    new_records_added = 0

    if state["next_shard_index"] >= len(shard_queries):
        state = {"next_shard_index": 0, "next_offset": 0}

    for shard_index in range(state["next_shard_index"], len(shard_queries)):
        if new_records_added >= max_papers:
            break

        shard_query = shard_queries[shard_index]
        print(f"Starting shard {shard_index + 1}/{len(shard_queries)}: {shard_query}")
        remaining = max_papers - new_records_added
        start_offset = state["next_offset"] if shard_index == state["next_shard_index"] else 0
        shard_results, next_offset, shard_exhausted = collect_query_results(
            query=shard_query,
            seen_ids=seen_ids,
            max_new_records=min(SEARCH_RESULT_CAP, remaining),
            batch_size=batch_size,
            delay_seconds=delay_seconds,
            start_offset=start_offset,
        )
        collected.extend(shard_results)
        new_records_added += len(shard_results)
        print(
            f"Added {new_records_added} new papers this run "
            f"({len(collected)} total saved so far)"
        )

        if shard_exhausted:
            state = {"next_shard_index": shard_index + 1, "next_offset": 0}
        else:
            state = {"next_shard_index": shard_index, "next_offset": next_offset}

        if checkpoint_every and (shard_index + 1) % checkpoint_every == 0:
            save_records(collected, output_file=output_file)
            save_state(state, state_file=state_file)
            print(f"Checkpoint saved with {len(collected)} records")

    if state["next_shard_index"] >= len(shard_queries):
        state = {"next_shard_index": 0, "next_offset": 0}

    save_state(state, state_file=state_file)
    print(
        f"Finished run with {new_records_added} new papers added "
        f"({starting_total} -> {len(collected)} total)"
    )
    return collected


def crawl_bulk(query, max_papers=50000, delay_seconds=1.0, sort="paperId:asc"):
    token = None
    collected = []

    while len(collected) < max_papers:
        data = fetch_papers_bulk(query=query, token=token, sort=sort)
        batch = data.get("data", [])

        if not batch:
            break

        remaining = max_papers - len(collected)
        collected.extend(process_paper(paper) for paper in batch[:remaining])
        print(f"Collected {len(collected)} papers")

        token = data.get("token")
        if len(collected) >= max_papers or not token:
            break

        time.sleep(delay_seconds)

    return collected


def save_records(records, output_file=OUTPUT_FILE):
    write_json_atomic(records, output_file)


def write_json_atomic(payload, output_file):
    output_file = Path(output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output_file.parent,
        delete=False,
    ) as temp_file:
        json.dump(payload, temp_file, indent=2)
        temp_file.write("\n")
        temp_path = Path(temp_file.name)

    temp_path.replace(output_file)


def main():
    parser = argparse.ArgumentParser(description="Fetch papers from Semantic Scholar")
    parser.add_argument("--query", default="machine learning", help="Search query")
    parser.add_argument("--max-papers", type=int, default=1000, help="Maximum papers to fetch")
    parser.add_argument("--batch-size", type=int, default=100, help="Papers fetched per request")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between requests")
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=10,
        help="Save progress every N batches while using the default search API",
    )
    parser.add_argument(
        "--sharded",
        action="store_true",
        help="Use multiple standard Semantic Scholar search queries and deduplicate results",
    )
    parser.add_argument(
        "--bulk",
        action="store_true",
        help="Use Semantic Scholar bulk search pagination for large result sets",
    )
    parser.add_argument(
        "--sort",
        default="paperId:asc",
        help="Sort order for bulk search, for example paperId:asc or citationCount:desc",
    )
    parser.add_argument(
        "--output",
        default=str(OUTPUT_FILE),
        help="Path to save fetched papers JSON",
    )
    parser.add_argument(
        "--state-file",
        default=str(STATE_FILE),
        help="Path to the resume state JSON used by sharded crawling",
    )
    args = parser.parse_args()

    if args.sharded:
        papers = crawl_sharded(
            base_query=args.query,
            max_papers=args.max_papers,
            batch_size=args.batch_size,
            delay_seconds=args.delay_seconds,
            checkpoint_every=args.checkpoint_every,
            output_file=Path(args.output).resolve(),
            state_file=Path(args.state_file).resolve(),
        )
    elif args.bulk:
        papers = crawl_bulk(
            query=args.query,
            max_papers=args.max_papers,
            delay_seconds=args.delay_seconds,
            sort=args.sort,
        )
    else:
        papers = crawl(
            query=args.query,
            max_papers=args.max_papers,
            batch_size=args.batch_size,
            delay_seconds=args.delay_seconds,
            checkpoint_every=args.checkpoint_every,
            output_file=Path(args.output).resolve(),
        )
    output_file = Path(args.output).resolve()
    save_records(papers, output_file=output_file)
    print(f"Saved {len(papers)} records to {output_file}")


if __name__ == "__main__":
    main()
