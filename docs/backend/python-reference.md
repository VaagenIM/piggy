# Python Reference

This page documents every Python source file in the project.

## `run.py`

`run.py` is both the local development runner and the WSGI module imported by Gunicorn.

### Development Path

When executed directly:

- Reduces Werkzeug logging noise.
- Sets `USE_CACHE=0`.
- Sets `FLASK_DEBUG=1`.
- On the first Werkzeug process only, calls `checkout_branch("output")` inside `piggybank/`.
- Starts `npx livereload piggy,piggybank -e html,css,js,md`.
- Imports `create_app()`, injects devtools, and runs Flask on port `5001`.

### Production Path

When imported, it creates `app = create_app(debug=FLASK_DEBUG == "1")`.

### Functions

| Function | Purpose | Notes |
| --- | --- | --- |
| `cleanup()` | `atexit` hook that terminates child subprocesses. | Used for livereload process cleanup in local dev. |
| `checkout_branch(branch)` | Runs shell commands to stash, fetch, checkout, and pull a branch in `piggybank/`. | Uses `os.system`; only called automatically by direct development mode. |

## `piggy/__init__.py`

Defines global constants and the `AssignmentTemplate` enum.

### Constants

| Constant | Value | Meaning |
| --- | --- | --- |
| `PIGGYBANK_FOLDER` | `Path("piggybank")` | Content root. |
| `STATIC_FONTS_PATHS` | generated list | Font file paths relative to `static/fonts/`; exposed to templates. |
| `ASSIGNMENT_ROUTE` | `"main"` | URL prefix for content browsing. |
| `MEDIA_ROUTE` | `"img"` | URL prefix for content media. |
| `IMG_FMT` | `"webp"` | Default image extension used for headers/thumbnails. |
| `ASSIGNMENTS_TEMPLATE_FOLDER` | `"assignments"` | Template subfolder for assignment-level pages. |
| `ASSIGNMENT_FILENAME_REGEX` | `^.*Level[ _](\d+)[ _]-[ _](.+).md$` | Recognizes assignment markdown files and extracts the level number. |
| `ALLOWED_URL_CHARS_REGEX` | regex | Whitelist for normalized URL keys. |

### `AssignmentTemplate`

Maps content depth to template names:

| Enum | Index | Template |
| --- | ---: | --- |
| `ROOT` | 0 | `assignments/0-assignments_root.html` |
| `YEAR` | 1 | `assignments/1-year_level.html` |
| `CLASS` | 2 | `assignments/2-class_name.html` |
| `SUBJECT` | 3 | `assignments/3-subject.html` |
| `TOPIC` | 4 | `assignments/4-topic.html` |
| `ASSIGNMENT` | 5 | `assignments/5-assignment.html` |
| `LEVELS_DATA` | 6 | metadata-only pseudo-level used to pass sibling assignment level data into templates. |

Methods:

- `.template`: returns `assignments/{index}-{name}.html`.
- `.index`: returns numeric depth.
- `get_template_from_index(index)`: returns a template path or `None`.
- `get_template_name_from_index(index)`: returns the enum name string.
- `get_dictmap()`: returns `{template_name: index}`.

## `piggy/app.py`

Owns Flask application creation and page/media routing.

### `create_app(debug=False)`

Configures:

- Flask static folder.
- Flask-Squeeze.
- `SEND_FILE_MAX_AGE_DEFAULT`: 30 days in debug, default otherwise.
- Jinja autoescape disabled.
- ProxyFix for reverse-proxy `proto` and `host`.
- Jinja loader extended with the static directory so generated TurtleConverter templates/static includes can be resolved.
- Assignment blueprint at `/main`.
- Media blueprint at `/img`.
- Startup tasks.
- Global context processors and filters.
- Routes and error handler.
- Optional cache warmup.

### Context Processor Values

All templates receive:

| Name | Meaning |
| --- | --- |
| `ASSIGNMENT_URL_PREFIX` | `"main"` |
| `MEDIA_URL_PREFIX` | `"img"` |
| `piggymap` | frozen PIGGYMAP |
| `img_fmt` | `"webp"` |
| `github_pages` | truthy if `GITHUB_PAGES` is set |
| `AssignmentTemplate` | enum class |
| `themes` | parsed theme metadata from CSS files |
| `debug` | Flask debug flag |
| `static_fonts_paths` | font asset paths |
| `unfreeze` | helper to convert frozen dicts/Paths for templates |

### Template Filters

| Filter | Purpose |
| --- | --- |
| `sort_by_level` | Sorts `(link, assignment)` tuples by integer `assignment["level"]`. |
| `list_difference` | Removes items found in provided lists. Used by subject templates to separate content types. |
| `unescape` | HTML-unescapes a string, then re-escapes `<` and `>` for display safety. |

### Template Globals

| Global | Purpose |
| --- | --- |
| `get_template_name_from_index(i)` | Converts path depth into assignment template name for breadcrumbs/back buttons. Cached when enabled. |

### Routes

| Route | Handler | Purpose |
| --- | --- | --- |
| `/` | `index()` | Renders `index.html`. |
| `/settings` | `settings_page()` | Renders direct settings page with sanitized `return_to`. |
| `/service-worker.js` | `service_worker()` | Placeholder 204. |
| `/.well-known/<path>` | `ignored_routes()` | Silences browser/tooling requests. |
| `/static/turtleconvert/javascripts/output/<path>` | `ignored_routes()` | Silences unused TurtleConverter paths. |
| `/favicon.ico` | `favicon()` | Redirects to static Piggy icon. |
| `/main/` and `/main/<path>` | `get_assignment_wildcard()` | Main content route. Normalizes path and dispatches to `_render_assignment_wildcard()`. |
| `/main/<path>/lang/<lang>` | `get_assignment_wildcard_lang()` | Static Pages language route variant. |
| `/img/<wildcard>/media/<filename>` | `get_assignment_media_wildcard()` | Serves content media or generated fallback header image. |
| `/main/<wildcard>/attachments/<filename>` | `get_assignment_media_wildcard()` | Serves assignment attachments or placeholder image. |

### `sanitize_internal_return_path(value)`

Protects `/settings?return_to=...` from external redirects. Allows only internal absolute paths and query strings.

## `piggy/api.py`

Defines the `/api` blueprint.

### Endpoints

| Route | Handler | Output |
| --- | --- | --- |
| `/api/generate_thumbnail/<text>` | `generate_thumbnail()` | WebP image response. |
| `/api/<route>` | `api_route_json()` | JSON for a PIGGYMAP segment plus metadata. |
| `/api/` | `api_piggymap()` | Full processed PIGGYMAP JSON. |
| `/api/search-data` | `api_search_index()` | Flat search document list. |

### `generate_thumbnail(text, request=request)`

Inputs:

- Path text, HTML-unescaped and truncated to 50 characters.
- Query params: `bg_color`, `text_color`, `width`, `height`, `c`.
- `c` seeds a deterministic palette choice if colors are not explicitly provided.

Safety/limits:

- Colors strip leading `#`.
- Width/height are capped at `1000`.
- Output is converted to RGB and served as WebP.

## `piggy/piggybank.py`

Builds and reads PIGGYMAP.

### PIGGYMAP Shape

Directory nodes:

```python
{
    "Some_Folder": {
        "data": {...children...},
        "meta": {
            "name": "...",
            "description": "...",
            "system_path": Path("piggybank/..."),
            "type": "exercise"
        }
    }
}
```

Assignment leaf nodes:

```python
{
    "Assignment_Slug": {
        "path": Path("piggybank/.../Name Level 1 - Title.md"),
        "level": "1",
        "level_name": "Title",
        "heading": "Title",
        "meta": {...frontmatter and .oink data...},
        "translation_meta": {"eng": {...}}
    }
}
```

### Functions

| Function | Purpose |
| --- | --- |
| `load_meta_json(path)` | Reads `meta.json`, returns `{}` if missing, and defaults `name` from folder name. |
| `get_piggymap_segment_from_path(path, piggymap)` | Walks a normalized URL path and returns `(meta, segment)`. |
| `get_all_meta_from_path(path, piggymap)` | Collects metadata by depth for templates, including `levels_data` for assignment pages. |
| `get_assignment_data_from_path(path, piggymap)` | Finds the leaf assignment data for a path. |
| `get_template_from_path(path)` | Chooses a template from path depth. |
| `load_oink_file(path)` | Reads YAML from a same-name `.oink` file if present. No current `.oink` files were found, but support exists. |
| `get_frontmatter_from_file(path)` | Reads YAML frontmatter and fallback first `#` heading/title. Escapes values via MarkupSafe. |
| `generate_piggymap(path, max_levels=5, _current_level=0)` | Recursively scans content tree, folders, meta files, markdown assignments, and translations. |
| `stringify_paths(d)` | Converts `Path` objects to strings recursively for JSON/template use. |
| `unfreeze(d)` | Converts frozen dicts to normal dicts and stringifies paths. |

At import time, the module prints build timing and sets:

```python
PIGGYMAP = deepfreeze(generate_piggymap(PIGGYBANK_FOLDER))
```

## `piggy/caching.py`

Handles cache warming and assignment rendering.

### Functions

| Function | Purpose |
| --- | --- |
| `remove_turtleconverter_stylesheets(head)` | Removes generated TurtleConverter stylesheet links from assignment head HTML. |
| `simplify_turtleconverter_body(body)` | Keeps TurtleConverter's rendered markdown article but removes the invisible Material page shell around it. |
| `cache_directory(segment, fn, _path="")` | Recursively calls the assignment render function for folders, assignments, and available translations. |
| `_mdfile_to_sections_with_retry(path, retries=0)` | Calls TurtleConverter `mdfile_to_sections()` and retries once for a known temporary-file startup race. |
| `_render_assignment(p, extra_metadata=None)` | Converts one markdown file to HTML, builds metadata, language data, media paths, and renders the final assignment template. |
| `_render_assignment_wildcard(path="", lang="")` | Main renderer for `/main`: renders folder grid templates or dispatches to `_render_assignment()`. |

### TurtleConverter Inputs

`mdfile_to_sections()` is called with:

- `docs_folder=PIGGYBANK_FOLDER`
- `leading_url="/main"`
- `normalize_urls=True`
- Template `piggy/templates/assignments/tconvert_assignment_base.html`

### Render Context for Assignment Pages

`_render_assignment()` provides:

- `content`: TurtleConverter `sections`, including `head`, `body`, `heading`, and `meta`.
- `meta`: merged assignment and ancestor metadata.
- `current_language`: record from `LANGUAGES`.
- `supported_languages`: default language plus existing translations.
- `media_abspath`: `/img/<assignment parent>`
- `abspath`: `/main/<assignment path>`
- Leaf assignment fields such as `level`, `level_name`, `translation_meta`.

## `piggy/search.py`

Builds browser-side search data for Lunr.

### `parse_body(file_path)`

Returns `(snippet, tokens)` for one markdown file.

Snippet behavior:

- Strips frontmatter, code blocks, blockquotes, tables, headings, lists, images, HTML, and markup.
- Keeps link labels.
- Truncates to 400 characters.

Token behavior:

- Keeps code block contents but strips fences.
- Removes markdown/link/image noise.
- Lowercases and tokenizes alphanumeric words plus Norwegian letters.
- Removes Norwegian/English/web/layout stopwords.
- Counts frequencies.
- Repeats top 60 tokens 1-4 times to influence Lunr BM25 without sending full content.

### `build_search_index(piggymap)`

Walks PIGGYMAP and returns documents:

```json
{
  "id": "VG2/IT/...",
  "title": "Assignment title",
  "breadcrumb": ["VG2", "IT", "..."],
  "content": "display snippet",
  "body": "weighted tokens"
}
```

## `piggy/thumbnails.py`

Generates deterministic title cards with Pillow.

### Helpers

- `_seed_from_text(title, seed)`: md5-derived integer seed.
- `_hex_to_rgb(h)`: hex to RGB tuple.
- `_blend_color(hex1, hex2, factor)`: subtle accent blend.
- `_draw_*`: eight decorative pattern functions: stripes, halftone dots, blobs, diamonds, rings, chevrons, wave bands, cross-hatch.

### `create_thumbnail(title, bg_color, text_color, size)`

Process:

1. Seeds a `random.Random` from title and colors.
2. Creates a base RGB image.
3. Blends accent colors.
4. Chooses exactly one decorative pattern.
5. Chooses one available TTF font.
6. Wraps title and shrinks font until it fits.
7. Draws centered multiline text.

The function is cached when `USE_CACHE=1`.

## `piggy/utils.py`

Shared helpers.

### Cache and Images

| Function | Purpose |
| --- | --- |
| `lru_cache_wrapper(func)` | Enables/disables `functools.lru_cache()` based on `USE_CACHE`. |
| `serve_pil_image(pil_img)` | Serializes a Pillow image as WebP via Flask `send_file()`. |

### Paths, Languages, and Summaries

| Function | Purpose |
| --- | --- |
| `get_supported_languages(assignment_path)` | Returns default language plus translations that exist beside an assignment. |
| `normalize_path_to_str(path, replace_spaces=False, normalize_url=False, remove_ext=False)` | Normalizes slashes, spaces, URL-safe characters, and extensions. |
| `generate_summary_from_mkdocs_html(html_content)` | Uses BeautifulSoup to extract the first 197 characters from `article.md-content__inner`. |
| `normalize_url_str(text)` | Applies `ALLOWED_URL_CHARS_REGEX`, then collapses repeated underscores. |

### Theme Metadata

| Function/Class | Purpose |
| --- | --- |
| `get_themes()` | Lists `piggy/static/css/themes`, parses metadata, sorts by `id`. |
| `ParserState` | Tiny state enum for metadata parser. |
| `get_css_metadata(path)` | Reads `/* METADATA ... */` block from a CSS file. |
| `parse_css_metadata_value(key, value)` | Converts list fields, integer `id`, and boolean strings. |
| `set_css_metadata_value(metadata, key, value)` | Supports nested keys like `preview.background`. |

### API JSON Transform

`process_json_for_api(obj, exclude_keys=None)` recursively:

- Converts `Path` values into `file_path` and `/main/...` `url`.
- Adds default media thumbnails for `system_path`.
- Converts relative thumbnail values into absolute `/img/...` URLs.
- Excludes keys supplied in `exclude_keys`.
- Drops keys starting with `turtletranslate_`.

### Startup

| Function | Purpose |
| --- | --- |
| `generate_print_css()` | Inlines light theme variables into `base/print_overrides.css`. |
| `delete_turtleconverter_stylesheets()` | Old cleanup helper, currently unused. |
| `startup_tasks()` | Runs TurtleConverter static generation and print CSS generation. |

## `piggy/models.py`

Loads `piggy/data/language-data.json`.

- `get_languages()` reads JSON and adds each language key into the language object as `key`.
- `LANGUAGES` is initialized at import time.

Language records include fields like `name`, `flag`, `direction`, `script`, `locale`, `font`, and `country_code`.

## `piggy/exceptions.py`

Project exceptions and HTTP normalization.

| Name | Purpose |
| --- | --- |
| `DEFAULT_ERROR_MESSAGE_NAMES` | Overrides default Werkzeug names, currently 404. |
| `ERROR_MESSAGE_DESCRIPTIONS` | Human-facing themed descriptions by status code. |
| `normalize_http_exception(e)` | Converts Werkzeug or Piggy HTTP exceptions into `PiggyHTTPException`. |
| `PiggyException` | Base project exception. |
| `PiggyErrorException` | Non-HTTP project error. |
| `PiggyHTTPException` | Holds `message` and `status_code`; includes context-manager support for try/except behavior. |

## `piggy/devtools.py`

`inject_devtools(app)` registers an `after_request` hook that inserts the livereload script before `</body>` for successful HTML responses. It is only used by `run.py` in direct development mode.
