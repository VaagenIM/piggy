# Tooling and Deployment

This page documents project files outside the app package that affect development, CI, deployment, static builds, formatting, and dependency management.

## Root Files

| File | Purpose |
| --- | --- |
| `README.md` | Minimal install instructions and public links. |
| `pyproject.toml` | Python package metadata, dependencies, build backend, Ruff config. |
| `package.json` | JavaScript dev dependencies and Prettier/Jinja formatting config. |
| `package-lock.json` | NPM lock file. Ignored by `.gitignore`, but present locally. |
| `Dockerfile` | Multi-stage Python 3.12 image for production runtime. |
| `docker-compose.yml` | Local/container deployment configuration. |
| `entrypoint.sh` | Activates venv and runs Gunicorn with signal traps. |
| `.gitmodules` | Defines `piggybank` submodule from `VaagenIM/piggybank`, branch `output`. |
| `.gitattributes` | Normalizes text files to LF line endings. |
| `.gitignore` | Ignores local/editor/generated artifacts. |
| `.dockerignore` | Keeps non-runtime files out of Docker build context. |
| `.prettierignore` | Excludes generated/vendor/devtools files from Prettier. |

## Python Packaging

`pyproject.toml` declares package name `piggy`, version `0.1.0`, and dependencies:

- `flask~=3.1.3`
- `turtleconverter@git+https://github.com/sondregronas/turtleconverter@main`
- `gunicorn~=26.0.0`
- `pillow~=12.2.0`
- `beautifulsoup4~=4.14.3`
- `frozendict==2.4.7`
- `flask-squeeze==3.5.0`
- `MarkupSafe==3.0.3`

Dev extra:

- `ruff~=0.15.13`

Ruff is configured for Python 3.12, line length 120, and lint codes `E4`, `E7`, `E9`, and `F`.

## JavaScript Tooling

`package.json` declares:

- Runtime dependency: `upgrade`.
- Dev dependencies: `livereload`, `prettier`, `prettier-plugin-jinja-template`.

Prettier is configured with the Jinja plugin for `*.html` files, 2-space tabs in templates, semicolons, trailing commas, single quotes, and LF endings.

## Dockerfile

The Docker build has two stages:

### Builder

- Base image: `python:3.12`.
- Workdir: `/app`.
- Copies `pyproject.toml`.
- Creates `/app/venv`.
- Installs the package with `pip install .`.
- Copies `piggy`.

### Runner

- Base image: `python:3.12-slim`.
- Installs `tzdata` and `git`.
- Sets:
  - `AUTO_UPDATE=True`
  - `FLASK_DEBUG=0`
  - `USE_CACHE=1`
  - `TZ=Europe/Oslo`
- Copies venv from builder.
- Copies the repository into `/app`.
- Exposes TCP port `5000`.
- Runs `entrypoint.sh`.

## Docker Compose

`docker-compose.yml` defines one service named `app`:

- Builds from the current directory.
- Container name: `piggy`.
- Port mapping: `5000:5000`.
- Environment:
  - `AUTO_UPDATE=False`
  - `FLASK_DEBUG="0"`
  - `USE_CACHE="1"`
  - `WEB_CONCURRENCY=4`
  - `TZ=Europe/Oslo`
- Restart policy: `unless-stopped`.
- Mounts local `./piggybank` to `/app/piggybank`.

The volume mount means content can be updated independently from the image if desired.

## Entrypoint

`entrypoint.sh`:

1. Activates `venv/bin/activate`.
2. Defines `run_app()` to start:

   ```bash
   gunicorn --bind 0.0.0.0:5000 -t 60 --preload run:app
   ```

3. Stores Gunicorn PID.
4. Handles `TERM` by terminating the child process and exiting.
5. Handles `HUP` by terminating and restarting.

`--preload` imports and builds the app before workers fork. That means PIGGYMAP and warm cache behavior run at master startup.

## GitHub Actions

### `.github/workflows/ruff.yml`

Runs on push and pull request.

- Checks out repository.
- Runs `chartboost/ruff-action@v1` with `src: './piggy'`.

### `.github/workflows/prettier.yml`

Runs on push and pull request.

- Checks out repository.
- Sets up Node 24.
- Runs `npm i`.
- Runs `npx prettier . --check`.

### `.github/workflows/CD.yml`

Runs on pushes to `main` and `develop`.

- Sets image tag to `latest` on `main`, `edge` otherwise.
- Builds for `linux/amd64` and `linux/arm64/v8`.
- Logs into GitHub Container Registry.
- Uses Docker Buildx and GitHub Actions cache.
- Pushes the built image.

### `.github/workflows/pages.yml`

Builds the main static GitHub Pages site.

Triggers:

- `repository_dispatch` type `fill_piggybank`
- manual `workflow_dispatch`
- pushes to `main`

Flow:

1. Runs on a self-hosted runner.
2. Checks out `main`.
3. Installs `uv` and Python 3.12.
4. Removes prior `piggybank` and kills existing Gunicorn/Python processes.
5. Checks out `VaagenIM/piggybank` branch `output` using `PIGGYPAT`.
6. Installs app and Pages build dependencies.
7. Sets `GITHUB_PAGES=1` and `USE_CACHE=0`.
8. Starts Gunicorn on `0.0.0.0:55555`.
9. Runs `.github/workflows/web_scraper.py`.
10. Uploads `.github/workflows/demo` as a Pages artifact.
11. Deploys with `actions/deploy-pages`.

### `.github/workflows/pages-demo.yml`

Builds the develop/edge static site and publishes it to `VaagenIM/piggy-edge` branch `gh-pages`.

Differences from main Pages workflow:

- Runs on pushes to `develop`.
- Replaces `piggy.iktim.no` with `piglet.iktim.no` in `web_scraper.py`.
- Writes `piglet.iktim.no` to `demo/CNAME`.
- Clones `VaagenIM/piggy-edge`, replaces its gh-pages contents, commits, and force pushes.

### `.github/workflows/requirements-pages.txt`

Extra dependencies for the static scraper:

- `requests`
- `beautifulsoup4`
- TurtleConverter from GitHub
- `rjsmin`
- `rcssmin`

### `.github/workflows/web_scraper.py`

The static scraper is a Python script that turns the live Flask site into static files.

Important globals:

| Name | Meaning |
| --- | --- |
| `WORKERS` | Multiprocessing pool size, currently 16. |
| `links` | HTML routes to visit, initially `/` and `/404`. |
| `api_links` | Direct API routes to save, initially `/api/search-data`. |
| `visited` | Routes already processed. |
| `media_links` | Discovered media file URLs. |
| `url` | Local live server base: `http://127.0.0.1:55555`. |
| `cname` | Static public base URL. |
| `media_link_filetypes` | Extensions treated as media/download assets. |

Important functions:

| Function | Purpose |
| --- | --- |
| `unquote_path(path)` | URL-decodes and unescapes `&amp;`. |
| `get_html(link)` | Fetches a page, parses links/media, rewrites static edge cases, returns HTML and discovered links. |
| `clean_link(link, path)` | Normalizes relative links and strips anchors/colon fragments. |
| `get_links(html, path)` | Extracts internal non-static hrefs. |
| `get_media_links(html, path)` | Extracts internal `src` and media hrefs. |
| `_write_html(html, path)` | Writes fetched HTML into `demo/`. |
| `_download_media(link)` | Downloads binary/media assets into `demo/`. |
| `download_site()` | Crawls all pages and downloads media. |
| `api_transform(link)` | Maps a visited `/main/...` page to `/api/...`. |
| `_download_api_view(link)` | Saves API view JSON for visited content pages. |
| `_download_direct_api(link)` | Saves direct API links like `/api/search-data`. |
| `download_api_views()` | Fetches API JSON in parallel. |
| `_minify(path, filetype)` | Minifies CSS/JS unless already `.min.*`. |
| `minify_folder(folder)` | Minifies all static CSS/JS outputs. |

The script also generates TurtleConverter static files, copies `piggy/static` into `demo/static`, and minifies output assets.

## Dependabot

`.github/dependabot.yml` checks monthly updates for:

- pip dependencies at `/`
- npm dependencies at `/`
- GitHub Actions at `/`

Updates are grouped by ecosystem.

## Ignore Files

### `.gitignore`

Ignores editor folders, virtualenvs, caches, generated TurtleConverter output, `node_modules/`, `package-lock.json`, and generated `print_overrides.css`.

The file currently allows core project files and `piggy/` content explicitly via negation rules.

### `.dockerignore`

Keeps Docker build context small by ignoring the demo output and allowing only:

- `run.py`
- `pyproject.toml`
- `package.json`
- `entrypoint.sh`
- `piggy/`

### `.prettierignore`

Ignores:

- devtools templates
- vendored/minified JS modules
- vendored CSS

This prevents formatting churn in generated or third-party files.

## Submodule

`.gitmodules` defines `piggybank`:

```ini
[submodule "piggybank"]
  path = piggybank
  url = https://github.com/VaagenIM/piggybank
  branch = output
  ignore = all
```

Development code may checkout/pull this branch automatically through `run.py`.

## Local Commands

Install:

```bash
pip install .[dev]
npm install
```

Run dev:

```bash
python run.py
```

Run Ruff:

```bash
ruff check piggy
```

Run Prettier check:

```bash
npx prettier . --check
```

Run Docker Compose:

```bash
docker compose up --build
```

