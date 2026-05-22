# Piggy Developer Documentation

This folder documents Piggy for future development. It is intentionally written as a working map of the codebase rather than a marketing overview: where data comes from, how requests are rendered, which frontend files own which behavior, and how to add content safely.

Piggybank itself is content. These docs document its storage format and authoring rules, but not the individual lessons.

## Documentation Map

- [Backend Overview](backend/README.md): Flask app lifecycle, Python module map, environment variables, and runtime concepts.
- [Python Reference](backend/python-reference.md): every Python module and important function/class.
- [Rendering, APIs, and Caching](backend/api-and-rendering.md): routes, response flow, TurtleConverter rendering, search index, thumbnails, and error handling.
- [Content Authoring](backend/content-authoring.md): how `piggybank/` is structured, how to add folders, assignments, translations, media, and metadata.
- [Tooling and Deployment](backend/tooling-deployment.md): Docker, Gunicorn, GitHub Actions, static Pages scraper, formatting, linting, and config files.
- [Frontend Overview](frontend/README.md): frontend architecture, script and style load order, and how rendered pages fit together.
- [Templates](frontend/templates.md): every Jinja template, macro, partial, and page template.
- [CSS Reference](frontend/css.md): import order, CSS variables, themes, markdown styling, layout, components, and every CSS file.
- [JavaScript Reference](frontend/javascript.md): every JavaScript file, global APIs, events, storage keys, and module responsibilities.
- [Settings and Preferences](frontend/settings-preferences.md): reader preference model, settings UI, presets, storage, and data attributes.
- [Search and Navigation](frontend/search-and-navigation.md): search overlay, Lunr index, language selector, level selector, breadcrumbs, and back button.
- [Themes and Visual Effects](frontend/themes.md): theme metadata, CSS theme contract, animated themes, and how to add a theme.

## Project Shape

Piggy is a Flask application that renders a nested assignment/content bank from the `piggybank/` folder.

At startup:

1. Python imports `piggy.piggybank`.
2. `generate_piggymap()` recursively scans `piggybank/`.
3. The resulting structure is frozen into `PIGGYMAP`.
4. `create_app()` registers page, media, and API routes.
5. Optional startup tasks generate static TurtleConverter assets and print CSS.
6. Optional warm caching renders assignment paths into the app's LRU caches.

At request time:

1. `/main/...` maps a URL path onto a PIGGYMAP segment.
2. Folder-like levels render Jinja card grids.
3. Assignment leaf pages render Markdown through TurtleConverter.
4. Shared layout templates attach navigation, settings, search, CSS, and JavaScript.
5. Media paths under `/img/...` serve `media/` assets, while assignment attachments are served from `/main/.../attachments/...`.

## Top-Level Directories

| Path | Purpose |
| --- | --- |
| `piggy/` | The Flask package, templates, static assets, CSS, JS, fonts, and image assets. |
| `piggybank/` | Content tree. It is a submodule/content source, not application code. |
| `.github/workflows/` | CI, container publishing, and static site generation. |
| `docs/` | This documentation. |
| `node_modules/`, `.venv/`, `build/`, caches | Local/generated artifacts. They are not project source and are not documented file-by-file. |

## Source File Groups

| Group | Files | Where documented |
| --- | ---: | --- |
| Python | 11 project modules plus `run.py` | [Python Reference](backend/python-reference.md) |
| HTML/Jinja | 41 templates/partials/macros | [Templates](frontend/templates.md) |
| CSS | 69 CSS files, including vendor CSS | [CSS Reference](frontend/css.md) |
| JavaScript | 19 JS files, including vendor/minified Lunr | [JavaScript Reference](frontend/javascript.md) |
| Content | Markdown, JSON metadata, media, translations | [Content Authoring](backend/content-authoring.md) |
| Tooling/config | Docker, pyproject, package, workflows, ignores | [Tooling and Deployment](backend/tooling-deployment.md) |

## Important Terms

| Term | Meaning |
| --- | --- |
| Piggy | The Flask app and frontend that render content. |
| Piggybank | The content tree under `piggybank/`. |
| Piggymap | The frozen in-memory dictionary built from Piggybank. It is the central routing/data model. |
| Assignment | A markdown file whose filename matches `... Level <number> - <title>.md`. |
| Level | The numeric part extracted from an assignment filename. Multiple assignment files in one topic become switchable levels. |
| Topic type | `meta.json` field that can be `exercise`, `assignment`, or `information`, changing card behavior and navigation. |
| TurtleConverter | External dependency that converts markdown assignments into Material/MkDocs-like HTML sections. |

## Local Development Quick Start

Install Python package and JavaScript development dependencies:

```bash
pip install .[dev]
npm install
```

Run the local dev server:

```bash
python run.py
```

Development mode sets `USE_CACHE=0` and `FLASK_DEBUG=1`, starts livereload, checks out the `piggybank` submodule branch named `output`, and serves the app on `http://localhost:5001`.

Production-style entrypoint:

```bash
gunicorn --bind 0.0.0.0:5000 -t 60 --preload run:app
```

Docker Compose exposes the app on port `5000` and mounts local `./piggybank` into the container.

## Development Ground Rules

- Treat `PIGGYMAP` as derived data. Change content files or parsing logic, not the map directly.
- Treat `piggybank/` lesson files as content. Update the content format docs when changing naming, metadata, translations, media, or frontmatter behavior.
- Keep route prefixes in mind: assignments are under `/main`, media is under `/img`, API data is under `/api`.
- Frontend settings are driven by `data-*` attributes on `document.documentElement`; CSS reacts to those attributes.
- Theme metadata lives in CSS comment blocks and is parsed by Python at startup.
- Generated/dependency folders are not source of truth: `.venv/`, `node_modules/`, `build/`, caches, `__pycache__/`, `piggy/static/turtleconvert/`, and generated `print_overrides.css`.
