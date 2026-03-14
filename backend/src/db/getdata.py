import json
import time
from pathlib import Path

import requests
from requests import RequestException


SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "papers.json"
BASE_URL = "https://api.openalex.org/works"
BASE_PARAMS = {
    "search": "machine learning",
    "select": "id,title,cited_by_count,publication_year,doi,referenced_works",
    "mailto": "kavinpersonal.id06@gmail.com",
}
TARGET_RECORDS = 50000
PER_PAGE = 200
REQUEST_TIMEOUT = (10, 120)
REQUEST_DELAY_SECONDS = 0.12
MAX_RETRIES = 5
RETRY_BACKOFF_SECONDS = 2
SAVE_EVERY_BATCHES = 5


def fetch_page(session: requests.Session, cursor: str) -> dict:
    params = BASE_PARAMS | {"per-page": PER_PAGE, "cursor": cursor}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(BASE_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except RequestException as exc:
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Failed to fetch cursor {cursor!r} after {MAX_RETRIES} attempts"
                ) from exc

            wait_seconds = RETRY_BACKOFF_SECONDS * attempt
            print(
                f"Request failed on attempt {attempt}/{MAX_RETRIES}: {exc}. "
                f"Retrying in {wait_seconds} seconds..."
            )
            time.sleep(wait_seconds)


def fetch_records(target_records: int = TARGET_RECORDS) -> list[dict]:
    session = requests.Session()
    cursor = "*"
    papers = []
    batches_fetched = 0

    while len(papers) < target_records:
        payload = fetch_page(session, cursor)
        batch = payload.get("results", [])
        if not batch:
            break

        remaining = target_records - len(papers)
        papers.extend(batch[:remaining])
        batches_fetched += 1

        meta = payload.get("meta", {})
        next_cursor = meta.get("next_cursor")
        print(f"Fetched {len(papers)} records so far...")

        if batches_fetched % SAVE_EVERY_BATCHES == 0 or len(papers) >= target_records:
            save_records(papers)
            print(f"Checkpoint saved with {len(papers)} records")

        if len(papers) >= target_records or not next_cursor:
            break

        cursor = next_cursor
        time.sleep(REQUEST_DELAY_SECONDS)

    return papers


def save_records(records: list[dict]) -> None:
    OUTPUT_FILE.write_text(json.dumps(records, indent=2), encoding="utf-8")


def main() -> None:
    papers = fetch_records()
    save_records(papers)
    print(f"Saved {len(papers)} records to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()