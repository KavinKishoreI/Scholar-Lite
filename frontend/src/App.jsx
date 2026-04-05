import { useEffect, useRef, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";
const PAGE_SIZE = 5;

function formatYear(year) {
  return year ?? "Year unknown";
}

export default function App() {
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [suggestions, setSuggestions] = useState([]);
  const [results, setResults] = useState([]);
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

  return (
    <div className="page-shell">
      <div className="backdrop-grid" />
      <main className="app-card">
        <section className="hero">
          <p className="eyebrow">PowerSearch</p>
          <h1>Research search built on custom indexing, autocomplete, and caching.</h1>
          <p className="subcopy">
            Explore a 50K paper corpus with trie-based autocomplete and paginated search
            powered by your in-memory engine.
          </p>
        </section>

        <section className="search-panel">
          <form className="search-form" onSubmit={handleSubmit}>
            <label className="search-label" htmlFor="query-input">
              Search papers
            </label>
            <div className="search-row">
              <input
                id="query-input"
                className="search-input"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Try deep learning, graph neural, machine learning..."
              />
              <button className="search-button" type="submit" disabled={loadingSearch}>
                {loadingSearch ? "Searching..." : "Search"}
              </button>
            </div>
          </form>

          {(loadingAuto || suggestions.length > 0) && (
            <div className="suggestion-box">
              <div className="suggestion-header">
                <span>Autocomplete</span>
                {loadingAuto && <span className="muted">Loading...</span>}
              </div>
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

        <section className="results-panel">
          <div className="results-topbar">
            <div>
              <p className="results-label">Results</p>
              <h2>{query ? `Showing matches for "${query}"` : "Run a search to begin"}</h2>
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
              <article key={paper.id} className="paper-card">
                <div className="paper-header">
                  <h3>{paper.title}</h3>
                  <span className="paper-year">{formatYear(paper.year)}</span>
                </div>
                <p className="paper-abstract">
                  {paper.abstract?.trim()
                    ? paper.abstract
                    : "No abstract available for this paper in the current dataset."}
                </p>
                <div className="paper-footer">
                  <span>Citations: {paper.cited_by_count ?? 0}</span>
                  {paper.paper_url && (
                    <a href={paper.paper_url} target="_blank" rel="noreferrer">
                      Open paper
                    </a>
                  )}
                </div>
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
            <span className="page-indicator">
              {query ? `${offset + 1}-${Math.min(offset + PAGE_SIZE, total)} of ${total}` : "No page"}
            </span>
            <button
              className="pager-button"
              type="button"
              onClick={() => runSearch(query, offset + PAGE_SIZE)}
              disabled={!query || !canGoNext() || loadingSearch}
            >
              Next
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}
