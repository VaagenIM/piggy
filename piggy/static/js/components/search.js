/**
 * Piggy Global Search
 */
(function () {
  "use strict";

  const INDEX_URL = "/api/search-data";

  let lunrIndex = null;
  let documents = {};
  let overlay = null;
  let input = null;
  let resultsContainer = null;
  let searchButton = null;

  // ── Bootstrap ────────────────────────────────────────────────────────────────

  function init() {
    overlay = document.getElementById("search-overlay");
    input = document.getElementById("search-overlay-input");
    resultsContainer = document.getElementById("search-results");
    searchButton = document.getElementById("search-button");

    if (!overlay || !input || !resultsContainer || !searchButton) return;

    searchButton.addEventListener("click", openSearch);

    document
      .getElementById("search-overlay-close")
      ?.addEventListener("click", closeSearch);

    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) closeSearch();
    });

    document.addEventListener("keydown", function (e) {
      if ((e.key === "k" || e.key === "K") && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        isOpen() ? closeSearch() : openSearch();
      }
      if (e.key === "Escape" && isOpen()) closeSearch();
    });

    input.addEventListener("input", onInput);

    // Build index eagerly in the background
    buildIndex();
  }

  function isOpen() {
    return !overlay.hidden;
  }

  function openSearch() {
    overlay.hidden = false;
    overlay.setAttribute("aria-hidden", "false");
    input.value = "";
    resultsContainer.innerHTML = "";
    input.focus();
  }

  function closeSearch() {
    overlay.hidden = true;
    overlay.setAttribute("aria-hidden", "true");
    searchButton.focus();
  }

  // ── Index ─────────────────────────────────────────────────────────────────

  function buildIndex() {
    fetch(INDEX_URL)
      .then((r) => r.json())
      .then(function (docs) {
        docs.forEach(function (doc) {
          documents[doc.id] = doc;
        });
        lunrIndex = window.lunr(function () {
          this.ref("id");
          this.field("title", { boost: 10 });
          this.field("content", { boost: 2 });
          this.field("body", { boost: 1 });
          docs.forEach((doc) => this.add(doc));
        });
        // Re-run if the user already typed while we were loading
        if (isOpen() && input.value.trim()) onInput();
      })
      .catch(function (err) {
        console.warn("Piggy search: failed to build index", err);
      });
  }

  // ── Search ───────────────────────────────────────────────────────────────────

  /**
   * Return a short excerpt of text around the first matching query term,
   * with matched words wrapped in <mark>.
   */
  function getSnippet(text, query) {
    if (!text) return "";
    const words = query
      .toLowerCase()
      .replace(/[~*^+\-:]/g, " ")
      .split(/\s+/)
      .filter(Boolean);
    const lower = text.toLowerCase();
    let best = -1;
    for (const w of words) {
      const idx = lower.indexOf(w);
      if (idx !== -1 && (best === -1 || idx < best)) best = idx;
    }
    if (best === -1) return text.slice(0, 160);
    const start = Math.max(0, best - 60);
    const end = Math.min(text.length, best + 120);
    let snippet =
      (start > 0 ? "…" : "") +
      text.slice(start, end) +
      (end < text.length ? "…" : "");
    for (const w of words) {
      snippet = snippet.replace(new RegExp(`(${w})`, "gi"), "<mark>$1</mark>");
    }
    return snippet;
  }

  /** Decode HTML entities in a string (e.g. &amp; → &) */
  function decodeEntities(str) {
    const txt = document.createElement("textarea");
    txt.innerHTML = String(str);
    return txt.value;
  }

  /** Build a breadcrumb of linked segments from the id path (excluding the leaf). */
  function getBreadcrumb(id) {
    const parts = id.split("/").slice(0, -1);
    if (!parts.length) return "";
    return parts
      .map(function (part, i) {
        const href = "/main/" + parts.slice(0, i + 1).join("/");
        const label = escapeHtml(decodeEntities(part.replace(/_/g, " ")));
        return `<a class="search-result-breadcrumb-link" href="${href}">${label}</a>`;
      })
      .join('<span class="search-result-breadcrumb-sep"> › </span>');
  }

  function onInput() {
    const query = input.value.trim();
    if (!query) {
      resultsContainer.innerHTML = "";
      return;
    }
    if (!lunrIndex) {
      resultsContainer.innerHTML =
        '<li class="search-result-message">Laster inn søkeindeks…</li>';
      return;
    }

    let raw;
    try {
      // Build a per-term query: exact match + fuzzy edit distance based on word length + wildcard prefix
      const terms = query
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map((t) => t.replace(/[~*^+\-:]/g, ""));
      const built = terms
        .map((t) => {
          // Short words: only ~1 fuzz to avoid too many false positives
          // Longer words: ~2 to catch typos/variants
          const fuzz = t.length <= 5 ? "~1" : "~2";
          return `${t}${fuzz} ${t}*`;
        })
        .join(" ");

      raw = lunrIndex.search(built);
    } catch (_) {
      try {
        raw = lunrIndex.search(query);
      } catch (__) {
        raw = [];
      }
    }

    if (!raw.length) {
      resultsContainer.innerHTML =
        '<li class="search-result-message">Ingen resultater funnet.</li>';
      return;
    }

    resultsContainer.innerHTML = raw
      .slice(0, 20)
      .map(function (r) {
        const doc = documents[r.ref];
        if (!doc) return "";
        const title = escapeHtml(decodeEntities(doc.title));
        const idParts = doc.id.split("/");
        const breadcrumb =
          Array.isArray(doc.breadcrumb) && doc.breadcrumb.length
            ? doc.breadcrumb
                .map((label, i) => {
                  const href = "/main/" + idParts.slice(0, i + 1).join("/");
                  return `<a class="search-result-breadcrumb-link" href="${escapeHtml(href)}">${escapeHtml(decodeEntities(label))}</a>`;
                })
                .join('<span class="search-result-breadcrumb-sep"> › </span>')
            : getBreadcrumb(doc.id);
        const snippetSource = doc.content || "";
        const snippet = getSnippet(snippetSource, query);
        const url = "/main/" + doc.id;

        return `<li class="search-result-item">
          ${breadcrumb ? `<span class="search-result-breadcrumb">${breadcrumb}</span>` : ""}
          <a class="search-result-link" href="${escapeHtml(url)}">
            <span class="search-result-title">${title}</span>
            ${snippet ? `<span class="search-result-desc">${snippet}</span>` : ""}
          </a>
        </li>`;
      })
      .join("");
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ── Init ─────────────────────────────────────────────────────────────────────

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
