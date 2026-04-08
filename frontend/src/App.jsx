import { useEffect, useRef, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
const PAGE_SIZE = 10;

function SearchIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" className="search-icon-svg">
      <path
        d="M10.5 4a6.5 6.5 0 1 0 4.03 11.6l4.43 4.43 1.06-1.06-4.43-4.43A6.5 6.5 0 0 0 10.5 4Zm0 1.5a5 5 0 1 1 0 10 5 5 0 0 1 0-10Z"
        fill="currentColor"
      />
    </svg>
  );
}

function formatYear(year) {
  return year ?? "Year unknown";
}

export default function App() {
  const ABSTRACT_PREVIEW_LENGTH = 260;
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [results, setResults] = useState([]);
  const [expandedAbstracts, setExpandedAbstracts] = useState({});
  const [offset, setOffset] = useState(0);
  const [total, setTotal] = useState(0);
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [loadingAuto, setLoadingAuto] = useState(false);
  const [error, setError] = useState("");
  const debounceRef = useRef(null);

  useEffect(() => {
    if (!draft.trim()) {
      setSuggestions([]);
      return;
    }

    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(async () => {
      const startedAt = performance.now();
      try {
        setLoadingAuto(true);
        const params = new URLSearchParams({ q: draft, k: "5" });
        const response = await fetch(`${API_BASE}/autocomplete?${params.toString()}`);
        const payload = await response.json();
        const elapsedMs = performance.now() - startedAt;
        console.log("[frontend] autocomplete", {
          query: draft,
          limit: 5,
          elapsed_ms: Number(elapsedMs.toFixed(3)),
          returned: payload.results?.length ?? 0,
        });
        setSuggestions(payload.results ?? []);
      } catch (fetchError) {
        const elapsedMs = performance.now() - startedAt;
        console.log("[frontend] autocomplete failed", {
          query: draft,
          limit: 5,
          elapsed_ms: Number(elapsedMs.toFixed(3)),
          error: fetchError.message,
        });
        setSuggestions([]);
      } finally {
        setLoadingAuto(false);
      }
    }, 180);

    return () => window.clearTimeout(debounceRef.current);
  }, [draft]);

  async function runSearch(nextQuery, nextOffset = 0) {
    if (!nextQuery.trim()) {
      setResults([]);
      setTotal(0);
      setQuery("");
      setOffset(0);
      setError("");
      return;
    }

    const startedAt = performance.now();
    try {
      setLoadingSearch(true);
      setError("");
      const response = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: nextQuery,
          offset: nextOffset,
          limit: PAGE_SIZE,
        }),
      });

      if (!response.ok) {
        throw new Error(`Search failed with status ${response.status}`);
      }

      const payload = await response.json();
      const elapsedMs = performance.now() - startedAt;
      console.log("[frontend] search", {
        query: nextQuery,
        offset: nextOffset,
        limit: PAGE_SIZE,
        elapsed_ms: Number(elapsedMs.toFixed(3)),
        total: payload.total ?? 0,
        returned: payload.results?.length ?? 0,
      });
      setQuery(nextQuery);
      setDraft(nextQuery);
      setOffset(nextOffset);
      setResults(payload.results ?? []);
      setExpandedAbstracts({});
      setTotal(payload.total ?? 0);
      setSuggestions([]);
    } catch (fetchError) {
      const elapsedMs = performance.now() - startedAt;
      console.log("[frontend] search failed", {
        query: nextQuery,
        offset: nextOffset,
        limit: PAGE_SIZE,
        elapsed_ms: Number(elapsedMs.toFixed(3)),
        error: fetchError.message,
      });
      setError(fetchError.message || "Something went wrong.");
    } finally {
      setLoadingSearch(false);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    runSearch(draft, 0);
  }

  function canGoPrev() {
    return offset > 0;
  }

  function canGoNext() {
    return offset + PAGE_SIZE < total;
  }

  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const pageNumbers = [];
  const pageWindowStart = Math.max(1, currentPage - 2);
  const pageWindowEnd = Math.min(totalPages, pageWindowStart + 4);

  for (let page = pageWindowStart; page <= pageWindowEnd; page += 1) {
    pageNumbers.push(page);
  }

  function toggleAbstract(paperId) {
    setExpandedAbstracts((current) => ({
      ...current,
      [paperId]: !current[paperId],
    }));
  }

  return (
    <div className="page-shell">
      <div className="backdrop-grid" />
      <main className="app-card">
        <section className="hero">
          <p className="eyebrow">Scholar-lite</p>
          <h1>Search scholarly papers with a fast, focused interface.</h1>
          <p className="subcopy">
            Explore a 50K paper corpus with trie-based autocomplete and paginated
            search powered by a custom in-memory engine.
          </p>
        </section>

        <section className="search-panel">
          <form className="search-form" onSubmit={handleSubmit}>
            <div className="search-shell">
              <SearchIcon />
              <input
                id="query-input"
                className="search-input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Try deep learning, graph neural, machine learning..."
              />
              <button className="search-icon-button" type="submit" disabled={loadingSearch}>
                <SearchIcon />
              </button>
            </div>
          </form>

          {(loadingAuto || suggestions.length > 0) && (
            <div className="suggestion-box">
              {loadingAuto && <div className="suggestion-loading">Loading...</div>}
              {suggestions.map((paper) => (
                <button
                  key={paper.id}
                  className="suggestion-item"
                  type="button"
                  onClick={() => runSearch(paper.title || draft, 0)}
                >
                  <span>{paper.title}</span>
                  <span className="muted">{formatYear(paper.year)}</span>
                </button>
              ))}
            </div>
          )}
        </section>

        {(query || loadingSearch || error) && (
          <section className="results-panel">
            <div className="results-topbar">
              <div>
                <p className="results-label">Results</p>
                <h2>{query ? `Showing matches for "${query}"` : "Searching..."}</h2>
              </div>
              {query && (
                <div className="results-meta">
                  <span>{total.toLocaleString()} total</span>
                  <span>Page size {PAGE_SIZE}</span>
                </div>
              )}
            </div>

            {error && <p className="error-banner">{error}</p>}

            <div className="results-list">
              {results.map((paper) => (
                <article
                  key={paper.id}
                  className={`paper-card${paper.paper_url ? " clickable" : ""}`}
                  onClick={() => {
                    if (paper.paper_url) {
                      window.open(paper.paper_url, "_blank", "noreferrer");
                    }
                  }}
                  onKeyDown={(event) => {
                    if (paper.paper_url && (event.key === "Enter" || event.key === " ")) {
                      event.preventDefault();
                      window.open(paper.paper_url, "_blank", "noreferrer");
                    }
                  }}
                  role={paper.paper_url ? "link" : undefined}
                  tabIndex={paper.paper_url ? 0 : undefined}
                >
                  {(() => {
                    const abstractText = paper.abstract?.trim()
                      ? paper.abstract
                      : "No abstract available for this paper in the current dataset.";
                    const isExpandable = abstractText.length > ABSTRACT_PREVIEW_LENGTH;
                    const isExpanded = Boolean(expandedAbstracts[paper.id]);
                    const visibleAbstract =
                      isExpandable && !isExpanded
                        ? `${abstractText.slice(0, ABSTRACT_PREVIEW_LENGTH).trim()}...`
                        : abstractText;

                    return (
                      <>
                        <div className="paper-header">
                          <h3>{paper.title}</h3>
                          <span className="paper-year">{formatYear(paper.year)}</span>
                        </div>
                        <p className="paper-abstract">{visibleAbstract}</p>
                        {isExpandable && (
                          <button
                            type="button"
                            className="abstract-toggle"
                            onClick={() => toggleAbstract(paper.id)}
                          >
                            {isExpanded ? "Show less" : "Show more"}
                          </button>
                        )}
                        <div className="paper-footer">
                          <span>Citations: {paper.cited_by_count ?? 0}</span>
                          <span className="paper-link-hint">
                            {paper.paper_url ? "Click card to open paper" : "Paper link unavailable"}
                          </span>
                        </div>
                      </>
                    );
                  })()}
                </article>
              ))}

              {!loadingSearch && query && results.length === 0 && !error && (
                <div className="empty-state">No results found for this query.</div>
              )}
            </div>

            <div className="pagination-row">
              <button
                className="pager-button secondary"
                type="button"
                onClick={() => runSearch(query, Math.max(0, offset - PAGE_SIZE))}
                disabled={!query || !canGoPrev() || loadingSearch}
              >
                Previous
              </button>
              <div className="page-number-row">
                {pageNumbers.map((pageNumber) => (
                  <button
                    key={pageNumber}
                    className={`page-number-button${pageNumber === currentPage ? " active" : ""}`}
                    type="button"
                    onClick={() => runSearch(query, (pageNumber - 1) * PAGE_SIZE)}
                    disabled={!query || loadingSearch}
                  >
                    {pageNumber}
                  </button>
                ))}
              </div>
              <button
                className="pager-button"
                type="button"
                onClick={() => runSearch(query, offset + PAGE_SIZE)}
                disabled={!query || !canGoNext() || loadingSearch}
              >
                Next
              </button>
            </div>
            <div className="pagination-meta">
              <span className="page-indicator">
                {query ? `${offset + 1}-${Math.min(offset + PAGE_SIZE, total)} of ${total}` : "No page"}
              </span>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
