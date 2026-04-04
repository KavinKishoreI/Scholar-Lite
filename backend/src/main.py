from __future__ import annotations

import logging
from pathlib import Path
import sys
import time
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


CURRENT_DIR = Path(__file__).resolve().parent
ENGINE_DIR = CURRENT_DIR / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from query_router import QueryRouter  # noqa: E402


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("powersearch.api")

app = FastAPI(title="PowerSearch API", version="0.1.0")
query_router = QueryRouter()


class PaperResult(BaseModel):
    id: str | None = None
    title: str | None = None
    year: int | None = None
    paper_url: str | None = None
    cited_by_count: int | None = None
    abstract: str | None = None


class SearchResponse(BaseModel):
    query: str
    total: int
    offset: int
    limit: int
    results: list[PaperResult]


class AutocompleteResponse(BaseModel):
    query: str
    count: int
    limit: int
    results: list[PaperResult]


class SearchRequest(BaseModel):
    query: str
    offset: int = 0
    limit: int = 10


def serialize_paper(paper: dict[str, Any]) -> PaperResult:
    return PaperResult(
        id=paper.get("id"),
        title=paper.get("title"),
        year=paper.get("year"),
        paper_url=paper.get("paper_url"),
        cited_by_count=paper.get("citation_count") or paper.get("cited_by_count"),
        abstract=paper.get("abstract"),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search", response_model=SearchResponse)
def search(
    payload: SearchRequest,
) -> SearchResponse:
    q = payload.query
    offset = payload.offset
    limit = payload.limit

    if not q.strip():
        raise HTTPException(status_code=422, detail="query must not be empty")
    if offset < 0:
        raise HTTPException(status_code=422, detail="offset must be >= 0")
    if limit < 0 or limit > 100:
        raise HTTPException(status_code=422, detail="limit must be between 0 and 100")

    start_time = time.perf_counter()
    try:
        result_payload = query_router.search_ranked(q, limit=limit, offset=offset)
    except Exception as exc:  # pragma: no cover - defensive API boundary
        elapsed = time.perf_counter() - start_time
        logger.exception(
            "search failed q=%r offset=%d limit=%d elapsed_sec=%.6f",
            q,
            offset,
            limit,
            elapsed,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.perf_counter() - start_time
    logger.info(
        "search q=%r offset=%d limit=%d total=%d returned=%d elapsed_sec=%.6f",
        q,
        offset,
        limit,
        result_payload["total"],
        len(result_payload["results"]),
        elapsed,
    )

    return SearchResponse(
        query=q,
        total=result_payload["total"],
        offset=offset,
        limit=limit,
        results=[serialize_paper(paper) for paper in result_payload["results"]],
    )


@app.get("/autocomplete", response_model=AutocompleteResponse)
def autocomplete(
    q: str = Query(..., min_length=1, description="Autocomplete query"),
    k: int = Query(5, ge=0, le=20),
) -> AutocompleteResponse:
    start_time = time.perf_counter()
    try:
        results = query_router.auto_complete(q, k)
    except Exception as exc:  # pragma: no cover - defensive API boundary
        elapsed = time.perf_counter() - start_time
        logger.exception(
            "autocomplete failed q=%r k=%d elapsed_sec=%.6f",
            q,
            k,
            elapsed,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    elapsed = time.perf_counter() - start_time
    logger.info(
        "autocomplete q=%r k=%d returned=%d elapsed_sec=%.6f",
        q,
        k,
        len(results),
        elapsed,
    )

    return AutocompleteResponse(
        query=q,
        count=len(results),
        limit=k,
        results=[serialize_paper(paper) for paper in results],
    )
