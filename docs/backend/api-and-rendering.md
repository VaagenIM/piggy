# Rendering, APIs, and Caching

This page describes how a request becomes a rendered page or JSON response.

## Page Rendering Flow

For a typical assignment URL such as:

```text
/main/VG2/IT/Utvikling/Programmering_-_Logging/Logging_Level_1_-_Introduksjon_til_Logging
```

the flow is:

1. `get_assignment_wildcard()` strips leading/trailing `/`.
2. Spaces are normalized to underscores.
3. If the path depth is deeper than `AssignmentTemplate.ASSIGNMENT.index`, a 404 is raised.
4. If the path is an assignment leaf and no language was provided in the URL, the `lang` cookie is read.
5. `_render_assignment_wildcard(path, lang)` finds the PIGGYMAP segment.
6. If the path depth is not the assignment leaf, a folder/card template is rendered.
7. If the path depth is the assignment leaf, `_render_assignment()` renders the markdown file through TurtleConverter.
8. `templates/assignments/5-assignment.html` extends `layout.html`, injects TurtleConverter head content, and renders `content.body`.

## Folder Page Rendering

Folder pages are all rendered through `_render_assignment_wildcard()`:

| Depth | Template | Meaning |
| ---: | --- | --- |
| 0 | `assignments/0-assignments_root.html` | Root overview. |
| 1 | `assignments/1-year_level.html` | Year level such as `VG1`, `VG2`, `VG3`. |
| 2 | `assignments/2-class_name.html` | Class/program level. |
| 3 | `assignments/3-subject.html` | Subject page. Splits children by type. |
| 4 | `assignments/4-topic.html` | Topic page. Shows cards for levels. |
| 5 | `assignments/5-assignment.html` | Markdown assignment page. |

The renderer passes:

- `meta`: current and ancestor metadata.
- `segment`: child data for the current path.
- `path`: normalized URL path.
- `media_abspath`: `/img/<path>`.
- `abspath`: `/main/<path>`.

## Assignment Markdown Rendering

`_render_assignment(p, extra_metadata=None)` performs assignment rendering.

### Input Selection

- Default language uses the source markdown file.
- A translated language changes the path to `translations/<lang>/<filename>`.
- If translation rendering fails at the route level, the route falls back to the default language.

### TurtleConverter Output

`mdfile_to_sections()` returns a dict with HTML sections. Piggy relies on:

| Key | Used for |
| --- | --- |
| `head` | Extra assignment head HTML injected into `5-assignment.html`. |
| `body` | Assignment body HTML rendered with `|safe`. |
| `heading` | Assignment title shown above body. |
| `meta` | Converted markdown metadata, including title when present. |

Piggy strips generated TurtleConverter stylesheet links from `head` so the local CSS system remains in control. It also simplifies `body` before rendering: the hidden Material drawer/search/skip shell is removed, while the visible markdown wrapper classes (`md-main__inner`, `md-grid`, `md-content`, `md-content__inner`, `md-typeset`) are kept so layout and markdown CSS preserve the same appearance.

### Metadata Merge Order

`_render_assignment()` builds `all_metadata` from:

1. Assignment leaf metadata/frontmatter.
2. Ancestor metadata collected by `get_all_meta_from_path()`.
3. Extra metadata passed from folder renderer.
4. `sections["meta"]["title"]` if TurtleConverter provides it.

If no summary exists, Piggy generates one from rendered HTML with BeautifulSoup.

## Media Routing

Media files are served by `get_assignment_media_wildcard()`.

### Content Media

```text
/img/<content path>/media/<filename>
```

Resolves to:

```text
piggybank/<content path>/media/<filename>
```

If a media file is missing and the request is for a `media/` file, Piggy generates a fallback header thumbnail using `/api/generate_thumbnail`.

### Assignment Attachments

```text
/main/<assignment path>/attachments/<filename>
```

Resolves to:

```text
piggybank/<topic folder>/attachments/<filename>
```

If an attachment is missing, Piggy returns `static/img/placeholders/100x100.png`.

### Language-Aware Attachments

For paths containing `/lang/<lang>/attachments/...`, the route removes the language suffix and assignment name from the wildcard before resolving the topic folder.

## JSON APIs

All API output goes through `process_json_for_api()` where needed so internal `Path` objects become frontend-friendly URLs.

### `/api/`

Returns the full processed PIGGYMAP.

Use this when a frontend or external tool needs the whole content tree.

### `/api/<path:route>`

Returns:

```json
{
  "meta": {},
  "segment": {}
}
```

- `meta` is metadata for the path.
- `segment` is the child data at the path.
- `translation_meta` is excluded from `segment` to reduce payload size.

### `/api/search-data`

Returns the flat document list used by Lunr:

```json
[
  {
    "id": "VG2/IT/...",
    "title": "Title",
    "breadcrumb": ["VG2", "IT"],
    "content": "Short snippet",
    "body": "weighted token token ..."
  }
]
```

The browser builds the Lunr index from this response.

### `/api/generate_thumbnail/<text>`

Returns generated WebP image bytes.

Supported query parameters:

| Param | Meaning |
| --- | --- |
| `bg_color` | Background hex color. Optional. |
| `text_color` | Text hex color. Optional. |
| `width` | Pixel width. Max 1000. |
| `height` | Pixel height. Max 1000. |
| `c` | Seed string for deterministic palette selection. |

## Search Index Generation

`build_search_index(PIGGYMAP)` recursively finds assignment leaves.

For each markdown file:

- `parse_body()` strips frontmatter and builds a display snippet.
- It produces a reduced weighted token string for Lunr.
- Breadcrumb labels come from folder `meta.name` when available.
- URLs are reconstructed on the frontend as `/main/<id>`.

Search is intentionally split:

- Backend knows content and can pre-process markdown efficiently.
- Frontend owns query interaction, fuzzy matching, keyboard shortcuts, and display.

## Cache Warmup

When `USE_CACHE=1`, `create_app()` calls:

```python
cache_directory(PIGGYMAP, fn=get_assignment_wildcard)
```

`cache_directory()`:

- Calls the render function for each folder.
- Calls it for each assignment.
- Calls it for each translation file that exists.
- Stops at assignment depth.

This warms Python LRU caches and catches missing assignment paths early.

## Cached Functions

The following important functions are cached through `lru_cache_wrapper()` when cache is enabled:

- `get_piggymap_segment_from_path()`
- `get_template_from_path()`
- `unfreeze()`
- `get_assignment_wildcard()`
- `get_assignment_wildcard_lang()`
- `_render_assignment()`
- `_render_assignment_wildcard()`
- `api_route_json()`
- `api_piggymap()`
- `api_search_index()`
- `create_thumbnail()`
- path/theme/language helper functions in `utils.py`

Development usually sets `USE_CACHE=0` so content and templates update without stale cached responses.

## Static Pages Generation

The GitHub Pages workflows do not use Flask as a runtime. Instead:

1. Start Gunicorn locally on `127.0.0.1:55555`.
2. Run `.github/workflows/web_scraper.py`.
3. The scraper crawls internal links, downloads media, downloads API views, copies static assets, minifies CSS/JS, and writes a static `demo/` directory.
4. The static directory is deployed to GitHub Pages or the `piggy-edge` repository.

Special static handling:

- `/lang/<lang>` links are rewritten for translated static pages.
- `/api/generate_thumbnail/...?...` is rewritten to `.webp`.
- `/media/header?...` query links are normalized to `media/header.webp`.
- API routes are saved as `index.json` under matching `/api/...` directories.

## Error Pages

Non-debug errors are normalized and rendered through `error.html`.

| Source | Result |
| --- | --- |
| Flask/Werkzeug `HTTPException` | Converted to `PiggyHTTPException`. |
| `PiggyHTTPException` | Used directly. |
| Unknown exception | Converted to 500. |

The error template always starts with the base 404 image and switches to a theme-specific image for selected themes by watching `data-theme` on `<html>`.
