# Backend Overview

Piggy's backend is a compact Flask application. Most of the work is not a database lookup, but a deterministic scan of `piggybank/` into `PIGGYMAP`, then URL-to-map rendering.

## Backend Responsibilities

- Build the content map from `piggybank/`.
- Render folder levels and assignment pages.
- Serve media and generated thumbnails.
- Expose JSON APIs for content metadata and search.
- Generate static support files from TurtleConverter.
- Provide cache behavior that can be disabled during development.
- Normalize application errors into themed error pages.

## Runtime Lifecycle

1. `run.py` imports `create_app()` for production or development.
2. Importing `piggy.piggybank` builds `PIGGYMAP`.
3. `create_app(debug=False)` configures Flask, Squeeze, Jinja loaders, proxy handling, context processors, template filters, and blueprints.
4. `startup_tasks()` generates TurtleConverter static files and writes `piggy/static/css/base/print_overrides.css`.
5. When `USE_CACHE=1`, `cache_directory()` walks PIGGYMAP and pre-renders assignment paths through cached functions.
6. Requests are handled by Flask routes registered in `piggy/app.py` and `piggy/api.py`.

## Main Data Flow

```text
piggybank files
  -> generate_piggymap()
  -> frozen PIGGYMAP
  -> /main route lookup
  -> folder template or TurtleConverter markdown render
  -> layout.html
  -> frontend assets and runtime behavior
```

## Route Prefixes

| Prefix | Constant | Purpose |
| --- | --- | --- |
| `/main` | `ASSIGNMENT_ROUTE` | All content browsing and assignment pages. |
| `/img` | `MEDIA_ROUTE` | Content `media/` files and generated fallback headers. |
| `/api` | API blueprint | JSON metadata, search data, generated thumbnails. |
| `/static` | Flask static folder | App CSS, JS, fonts, icons, generated TurtleConverter assets. |

## Environment Variables

| Variable | Used by | Meaning |
| --- | --- | --- |
| `USE_CACHE` | `utils.lru_cache_wrapper()`, `create_app()` | `"1"` enables LRU caching and warm render cache. `"0"` leaves functions uncached, useful during development. |
| `FLASK_DEBUG` | `run.py`, `create_app()` | `"1"` enables debug behavior. In debug, errors are re-raised instead of themed error pages. |
| `GITHUB_PAGES` | `create_app()`, templates | Enables language-in-URL behavior for static Pages output. |
| `WEB_CONCURRENCY` | Gunicorn/runtime | Worker count in deployment environments. Compose sets it to 4. |
| `AUTO_UPDATE` | Docker/env only | Present in Docker config, currently not consumed by Python code. |
| `TZ` | Docker/env | Container timezone. |

## Python File Map

| File | Role |
| --- | --- |
| `run.py` | Entrypoint for local development and production WSGI. |
| `piggy/__init__.py` | Project constants and `AssignmentTemplate` enum. |
| `piggy/app.py` | Flask app factory, page routes, media routes, context processors, filters, error handler. |
| `piggy/api.py` | API blueprint for thumbnails, metadata, full piggymap, and search data. |
| `piggy/piggybank.py` | Piggymap builder and path/metadata lookup helpers. |
| `piggy/caching.py` | Cache warmer and assignment rendering functions. |
| `piggy/search.py` | Markdown snippet/token extraction and flat search index builder. |
| `piggy/thumbnails.py` | Deterministic Pillow thumbnail generation. |
| `piggy/utils.py` | Cache wrapper, path normalization, theme metadata parsing, JSON API transforms, startup tasks. |
| `piggy/models.py` | Language-data loader. |
| `piggy/exceptions.py` | Project exception types and HTTP exception normalization. |
| `piggy/devtools.py` | Local livereload injection for HTML responses. |

See [Python Reference](python-reference.md) for function-level detail.

## Backend Dependencies

Declared in `pyproject.toml`:

- Flask for HTTP routing and templates.
- TurtleConverter from GitHub for markdown conversion and static assets.
- Gunicorn for production serving.
- Pillow for generated thumbnails.
- BeautifulSoup for summary generation and static scraper support.
- frozendict for freezing PIGGYMAP and cacheable metadata.
- Flask-Squeeze for response compression/minification support.
- MarkupSafe for escaped frontmatter values.
- Ruff as the only declared Python dev dependency.

## Caching Model

Caching is centralized through `lru_cache_wrapper()` in `piggy/utils.py`.

When `USE_CACHE=1`:

- Decorated lookup/render functions use `functools.lru_cache`.
- `create_app()` calls `cache_directory()` at startup.
- Rendered assignment responses and path lookups are reused.

When `USE_CACHE=0`:

- The wrapper returns the original function.
- Local content/template changes are easier to see without restarting for every cached value.

Important: cache keys must be hashable. Frozen metadata from `frozendict.deepfreeze()` is used where needed.

## Error Handling

`app.errorhandler(Exception)` catches all exceptions in non-debug mode.

- Werkzeug `HTTPException` values are converted into `PiggyHTTPException`.
- Unknown exceptions become status 500 with a generic message.
- `templates/error.html` picks themed 404 artwork based on the active theme.
- In debug mode, the original exception is raised.

## Extension Points

Common backend changes usually land in one of these places:

- Add a page-level route: `piggy/app.py`.
- Add a JSON endpoint: `piggy/api.py`.
- Change content discovery rules: `piggy/piggybank.py`.
- Change markdown rendering behavior: `piggy/caching.py` or TurtleConverter template files.
- Change search result fields/ranking source: `piggy/search.py` and `static/js/components/search.js`.
- Add a theme metadata field: `utils.get_css_metadata()` and settings frontend code.
- Add a new language option: `piggy/data/language-data.json`.

