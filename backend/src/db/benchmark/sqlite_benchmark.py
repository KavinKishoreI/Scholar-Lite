import json
import sqlite3
import sys
import time
from pathlib import Path


CURRENT_DIR = Path(__file__).resolve().parent
DB_DIR = CURRENT_DIR
DB_ROOT = CURRENT_DIR.parent
DATASET_PATH = DB_ROOT / "semantic_scholar_papers.json"
DB_PATH = DB_DIR / "semantic_scholar_benchmark.db"
ENGINE_DIR = DB_ROOT.parent / "engine"

if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from query_router import QueryRouter  # noqa: E402


def load_papers():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def rebuild_sqlite_db():
    papers = load_papers()
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE papers (
            paper_id TEXT PRIMARY KEY,
            title TEXT,
            abstract TEXT,
            year INTEGER,
            text_blob TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE VIRTUAL TABLE papers_fts
        USING fts5(paper_id UNINDEXED, title, abstract, text_blob)
        """
    )

    rows = []
    fts_rows = []
    for paper in papers:
        paper_id = paper.get("paper_id")
        title = paper.get("title") or ""
        abstract = paper.get("abstract") or ""
        year = paper.get("year")
        text_blob = f"{title} {abstract}".strip()
        rows.append((paper_id, title, abstract, year, text_blob))
        fts_rows.append((paper_id, title, abstract, text_blob))

    cur.executemany(
        "INSERT INTO papers (paper_id, title, abstract, year, text_blob) VALUES (?, ?, ?, ?, ?)",
        rows,
    )
    cur.executemany(
        "INSERT INTO papers_fts (paper_id, title, abstract, text_blob) VALUES (?, ?, ?, ?)",
        fts_rows,
    )
    conn.commit()
    conn.close()
    return len(papers)


def run_naive_like(conn, query, offset, limit):
    cur = conn.cursor()
    tokens = [token.lower() for token in query.split() if token]
    where_clause = " AND ".join(["LOWER(text_blob) LIKE ?" for _ in tokens]) or "1=1"
    params = [f"%{token}%" for token in tokens]

    start = time.perf_counter()
    total = cur.execute(
        f"SELECT COUNT(*) FROM papers WHERE {where_clause}",
        params,
    ).fetchone()[0]
    rows = cur.execute(
        f"""
        SELECT paper_id, title, year
        FROM papers
        WHERE {where_clause}
        ORDER BY COALESCE(year, 0) DESC
        LIMIT ? OFFSET ?
        """,
        params + [limit, offset],
    ).fetchall()
    elapsed = time.perf_counter() - start
    return elapsed, total, rows


def run_fts(conn, query, offset, limit):
    cur = conn.cursor()
    match_query = " AND ".join([f'"{token}"' for token in query.split() if token])

    start = time.perf_counter()
    total = cur.execute(
        "SELECT COUNT(*) FROM papers_fts WHERE papers_fts MATCH ?",
        (match_query,),
    ).fetchone()[0]
    rows = cur.execute(
        """
        SELECT p.paper_id, p.title, p.year
        FROM papers_fts f
        JOIN papers p ON p.paper_id = f.paper_id
        WHERE papers_fts MATCH ?
        ORDER BY COALESCE(p.year, 0) DESC
        LIMIT ? OFFSET ?
        """,
        (match_query, limit, offset),
    ).fetchall()
    elapsed = time.perf_counter() - start
    return elapsed, total, rows


def run_engine(query, offset, limit):
    router = QueryRouter()
    router.search_cache.nodes.clear()
    router.search_cache.head.next = router.search_cache.tail
    router.search_cache.tail.prev = router.search_cache.head

    start = time.perf_counter()
    payload = router.search_ranked(query, limit=limit, offset=offset)
    elapsed = time.perf_counter() - start
    return elapsed, payload["total"], payload["results"]


def main():
    count = rebuild_sqlite_db()
    print(f"Built SQLite benchmark DB at: {DB_PATH}")
    print(f"Inserted records: {count}")

    conn = sqlite3.connect(DB_PATH)
    queries = [
        ("deep learning", 0, 5),
        ("machine learning", 0, 5),
        ("graph neural", 0, 5),
    ]

    for query, offset, limit in queries:
        naive_elapsed, naive_total, naive_rows = run_naive_like(conn, query, offset, limit)
        fts_elapsed, fts_total, fts_rows = run_fts(conn, query, offset, limit)
        engine_elapsed, engine_total, engine_rows = run_engine(query, offset, limit)

        print()
        print(f"query={query!r} offset={offset} limit={limit}")
        print(
            f"naive_like total={naive_total} elapsed_sec={naive_elapsed:.6f} "
            f"first_title={naive_rows[0][1] if naive_rows else None}"
        )
        print(
            f"fts_indexed total={fts_total} elapsed_sec={fts_elapsed:.6f} "
            f"first_title={fts_rows[0][1] if fts_rows else None}"
        )
        print(
            f"engine total={engine_total} elapsed_sec={engine_elapsed:.6f} "
            f"first_title={engine_rows[0].get('title') if engine_rows else None}"
        )

    conn.close()


if __name__ == "__main__":
    main()
