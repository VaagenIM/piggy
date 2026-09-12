"""
A hacky script that scrapes a website and downloads all the pages and media files.
"""

import multiprocessing
import os
import re
import subprocess
import time
import requests
import json
from hashlib import sha256
from dataclasses import dataclass
from pathlib import Path
from shutil import copytree, rmtree
from urllib.parse import unquote
from bs4 import BeautifulSoup as bs
from turtleconverter import generate_static_files
from rjsmin import jsmin
from rcssmin import cssmin

WORKERS = max(1, multiprocessing.cpu_count() - 1)

links = {"/", "/404"}
api_links = {"/api/search-data"}
api_view_links = set()
visited = set()
media_links = set()
changed_media_links = set()
incremental_mode = False
url = "http://127.0.0.1:55555"  # The URL of the website we are scraping
cname = "https://piggy.iktim.no"  # The CNAME of the website we will push the demo to


@dataclass
class PageResult:
    html: str
    links: set[str]
    media_links: set[str]

# Media link are files that we want to download, but not parse as HTML (e.g. not write as UTF-8)
# specifically fonts are causing issues.
media_link_filetypes = [
    "ttf",
    "woff",
    "woff2",
    "eot",
    "svg",
    "otf",
    "css",
    "js",
    "pdf",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "mp4",
]


os.chdir(os.path.dirname(os.path.abspath(__file__)))


def unquote_path(path):
    new_path = unquote(path)
    new_path = new_path.replace("&amp;", "&")
    return new_path


def get_with_retry(url_to_fetch, *, timeout=600, max_attempts=3):
    """Retry HTML page fetches when the server temporarily responds with HTTP 500."""
    last_response = None
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url_to_fetch, allow_redirects=True, timeout=timeout)
        except requests.RequestException as exc:
            if attempt == max_attempts:
                raise
            print(f"WARNING: Request failed for {url_to_fetch} (attempt {attempt}/{max_attempts}): {exc}. Retrying...")
            time.sleep(attempt)
            continue

        last_response = response
        if response.status_code != 500:
            return response

        if attempt == max_attempts:
            print(
                f"WARNING: Could not fetch {url_to_fetch} after {max_attempts} attempts (status code: {response.status_code})"
            )
            return response

        print(
            f"WARNING: Could not fetch {url_to_fetch} (status code: {response.status_code}). Retrying attempt {attempt + 1}/{max_attempts}..."
        )
        time.sleep(attempt)

    return last_response


def get_html(link) -> PageResult | None:
    """Get the html from the given url, and append the new links to the links list."""
    page_url = f"{url}/{link.strip('/')}"
    print(f"Visiting \33[34m{page_url}\33[0m")
    r = get_with_retry(page_url)

    visited.add(link)

    if not r.ok and link not in ["/404"]:
        if link == "/":
            raise Exception("Could not fetch the main page. Is the server running?")
        print(f"WARNING: Could not fetch {link} (status code: {r.status_code})")
        return None

    # Only prettify if mimetype is text/html
    is_html = "text/html" in r.headers.get("Content-Type", "")
    if is_html:
        html = str(bs(r.text, "html.parser"))
    else:
        html = r.text

    new_links = get_links(html, path=link.strip("/"))

    # Get media links as long as we are not in the lang folder
    new_media_links = set()
    if "/lang/" not in link:
        new_media_links = get_media_links(html, path=link.strip("/"))

    # TODO: this is a hack. hopefully temporary.
    html = re.sub(r"""/api/generate_thumbnail/([^?]*)(\?[^"]*)""", r"/api/generate_thumbnail/\1.webp", html)
    html = re.sub(r"/media/header\..+\?title=[^\"]*", r"/media/header.webp", html)

    # Replace all content (og) links with the cname
    html = re.sub(rf"content=\"({url})([^\"/]*)", rf'content="{cname}\2', html)
    html = html.replace(url, cname)

    # A hack to fix media links
    if "/lang/" in link:
        lang = link.split("/lang/")[1].split("/")[0]
        html = re.sub(r'href="attachments/', 'href="../../attachments/', html)
        html = re.sub(r'src="attachments/', 'src="../../attachments/', html)
        html = re.sub(
            r'(content="[^"]*?)([\\/])translations[\\/][^"\\/]+[\\/](.*?)"\s+((?:property|name)="(?:og:image|twitter:image)")',
            r'\1\2\3" \4',
            html,
        )
        html = re.sub(
            rf"""href=\"({link.split("Level")[0].split("/")[-1]}[^/]+)\"""", rf'href="../../\1/lang/{lang}"', html
        )

    # Ensure parent directories of every discovered link are also visited.
    # Some pages (e.g. assignments) hide the parent topic directory from the
    # breadcrumbs, so the scraper would otherwise never discover it.
    parent_links = set()
    for l in new_links:
        parts = l.strip("/").split("/")
        for i in range(1, len(parts)):
            parent_links.add("/" + "/".join(parts[:i]))
    new_links |= parent_links

    # Remove links that are media links
    new_links -= new_media_links
    return PageResult(html, new_links, new_media_links)


def is_api_view_link(link: str) -> bool:
    """Return whether a successfully fetched page should have a static API view."""
    path = link.split("?", 1)[0].split("#", 1)[0].strip("/")
    if not path.startswith("main/"):
        return False
    return not any(segment in path.split("/") for segment in ("lang", "attachments", "media"))


def clean_link(link, path):
    if re.match(r"\.?.+[#:].*", link.split("/")[-1]) and path:
        # Reconstruct without #.* or :.*
        stem = link.split("/")[-1].split("#")[0].split(":")[0]
        directories = link.split("/")[:-1]
        link = "/".join(directories + [stem])
    # Add path to relative links
    if not link.startswith("/") and path:
        link = f"/{path.rsplit('/', 1)[0]}/{link}"
    # Replace \\ with /
    link = link.replace("\\", "/")
    return link


def get_links(html, path=""):
    links = re.compile(r'href="((?!#|https?://)[^"]*)"').findall(html)
    filtered_links = set()
    for link in links:
        if link == "javascript:void(0)":
            continue
        if link.startswith("/static/"):
            continue
        link = clean_link(link, path)
        filtered_links.add(link)

    shortlink_paths = re.compile(r'data-shortlink-url="https?://[^/"]+(/[^"]*)"').findall(html)
    filtered_links.update(shortlink_paths)

    return filtered_links


def get_media_links(html, path=""):
    media_src_regex = r'src="((?!#|https?://)[^"]+)"'
    media_href_regex = r'href="((?!#|https?://)[^"]+\.(' + "|".join(media_link_filetypes) + r'))"'
    media_links_regex = re.compile(rf"{media_src_regex}|{media_href_regex}")

    _media_links = media_links_regex.findall(html)
    _media_links = [link[0] or link[1] for link in _media_links]
    filtered_links = set()
    for link in _media_links:
        link = clean_link(link, path)
        if link.startswith("/static/"):
            continue
        if not link.startswith("/") and path:
            filtered_links.add(f"{path.rsplit('/', 1)[0]}/{link}")
            continue
        if "?" in link and any(
            (
                link.split("?")[0] in [l.split("?")[0] for l in media_links],
                link.split("?")[0] in [l.split("?")[0] for l in filtered_links],
            )
        ):
            print(
                f"Skipping {link} because it has a query string and the base link is already in media_links or filtered_links"
            )
            continue
        filtered_links.add(link)

    return filtered_links


def _write_html(html, path):
    os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
    with open(f"demo/{path}", "wb+") as f:
        f.write(html.encode())


def _download_media(link):
    request_path = link.strip("/").split("#")[0]
    path = request_path
    path = unquote_path(path)
    # TODO: this is a hack. hopefully temporary.
    if "/api/generate_thumbnail/" in link:
        path = path.rsplit("?")[0] + ".webp"
    path = path.rsplit("?")[0]
    output_path = Path("demo") / path
    if incremental_mode and output_path.exists():
        return

    print(f"Downloading \33[34m{link}\33[0m")
    r = requests.get(f"{url}/{request_path}", allow_redirects=True)
    try:
        os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
    except (NotADirectoryError, OSError):
        print(f"WARNING: Could not create directory for {path}. Skipping download.")
        return

    if not path or not r.ok:
        print(f"WARNING: Could not download {link}")
        return

    if len(path.split("/")[-1]) > 255:
        print("WARNING: Cannot download file with name longer than 255 characters")
        return
    try:
        os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
        with open(f"demo/{path}", "wb+") as f:
            f.write(r.content)
    except Exception as e:
        print(f"WARNING: Could not write file {path}: {e}")


def download_site():
    media_tasks = set(changed_media_links)
    with multiprocessing.Pool(processes=WORKERS) as pool:
        while visited != links:
            tasks = set(link for link in links if link not in visited)

            for link in tasks:
                visited.add(link)  # Mark as visited BEFORE calling get_html()

            results = pool.map(get_html, tasks)
            write_tasks = []

            for link, result in zip(tasks, results):
                if result is None:
                    continue

                if link == "/":
                    path = "index.html"
                else:
                    path = link.split("#")[0].strip("/")
                    if path.startswith("s/") and "." not in path:
                        path += "/index.html"
                    elif link.endswith("/") and "." not in path:
                        path += "/index.html"
                    elif "." not in path:
                        path += ".html"

                print(f"Writing \33[34m{link}\33[0m")
                write_tasks.append((result.html, path))
                if is_api_view_link(link):
                    api_view_links.add(link)

                if not incremental_mode:
                    links.update(result.links)
                media_tasks.update(result.media_links)
            pool.starmap(_write_html, write_tasks)
    # A separate pool for media tasks, as we don't want to download multiple media files at once
    # (this appears to happen when we download the media files in parallel with the html files)
    with multiprocessing.Pool(processes=WORKERS) as pool:
        pool.map(_download_media, media_tasks)  # Download media in parallel


def api_transform(link: str) -> str | None:
    # strip query/hash
    link = link.split("?")[0].split("#")[0]
    link = link.strip("/")

    if link == "":
        return "/api"
    elif not link.startswith("main/"):
        return None
    # Skip URLs that are translated, as they are (currently) not part of the API
    elif "/lang/" in link:
        return None

    link = link[len("main/") :]
    # remove file extensions
    link = re.sub(r"\.[a-zA-Z0-9]+$", "", link)

    return f"/api/{link}"


def _download_api_view(link):
    api_path = api_transform(link)

    # skip invalid mappings (like /static or /lang/)
    if not api_path:
        return

    print(f"Fetching API \33[34m{api_path}\33[0m")

    try:
        r = requests.get(f"{url}{api_path}", timeout=600)
    except Exception as e:
        print(f"WARNING: request failed for {api_path}: {e}")
        return

    if not r.ok:
        print(f"WARNING: failed {api_path} ({r.status_code})")
        return

    full_path = f"demo{api_path}/index.json"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    with open(full_path, "wb+") as f:
        f.write(r.content)


def _download_direct_api(link):
    """Download an /api/ link directly, saving it as index.json under demo/."""
    link = link.split("?")[0].split("#")[0]
    api_path = "/" + link.strip("/")
    print(f"Fetching API \33[34m{api_path}\33[0m")
    try:
        r = requests.get(f"{url}{api_path}", timeout=600)
    except Exception as e:
        print(f"WARNING: request failed for {api_path}: {e}")
        return
    if not r.ok:
        print(f"WARNING: failed {api_path} ({r.status_code})")
        return
    full_path = f"demo{api_path}/index.json"
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "wb+") as f:
        f.write(r.content)


def download_api_views():
    with multiprocessing.Pool(processes=WORKERS) as pool:
        pool.map(_download_api_view, api_view_links)
        pool.map(_download_direct_api, api_links)


def _minify(path, filetype):
    if path.name.endswith(f".min.{filetype}"):
        # Already minified, skip
        return
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        if filetype == "css":
            minified_content = cssmin(content)
        elif filetype == "js":
            minified_content = jsmin(content)
        else:
            raise ValueError(f"Unsupported filetype: {filetype}")
    except Exception as e:
        print(f"WARNING: Minification failed for {path}: {e}")
        minified_content = content
    with open(path, "w", encoding="utf-8") as f:
        f.write(minified_content)


def minify_folder(folder):
    for dirpath, _, filenames in os.walk(folder):
        for filename in filenames:
            p = Path(dirpath) / filename
            suffix = p.suffix.lower().lstrip(".")
            if suffix in ["css", "js"]:
                _minify(p, suffix)


def _git_revision(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def _changed_piggybank_files(
    piggybank_path: Path, previous_revision: str, current_revision: str
) -> list[tuple[str, str]]:
    outputs = [
        subprocess.check_output(
            [
                "git",
                "-c",
                "core.quotePath=false",
                "-C",
                str(piggybank_path),
                "diff",
                "--name-status",
                previous_revision,
                current_revision,
            ],
            text=True,
        ),
        subprocess.check_output(
            [
                "git",
                "-c",
                "core.quotePath=false",
                "-C",
                str(piggybank_path),
                "diff",
                "--name-status",
                current_revision,
            ],
            text=True,
        ),
    ]
    changes = []
    seen = set()
    for output in outputs:
        for line in output.splitlines():
            status, path = line.split(maxsplit=1)
            if path.replace("\\", "/").startswith("preview/"):
                continue
            change = (status[0], path)
            if change not in seen:
                changes.append(change)
                seen.add(change)
    return changes


def _piggybank_worktree_fingerprint(piggybank_path: Path) -> str:
    diff = subprocess.check_output(
        ["git", "-C", str(piggybank_path), "diff", "--binary", "HEAD"], stderr=subprocess.STDOUT
    )
    return sha256(diff).hexdigest()


def _worktree_fingerprint(repository_path: Path) -> str:
    diff = subprocess.check_output(
        ["git", "-C", str(repository_path), "diff", "--binary", "HEAD"], stderr=subprocess.STDOUT
    )
    return sha256(diff).hexdigest()


def _route_for_path(path: str) -> tuple[set[str], set[str], bool]:
    """Return affected HTML routes, deleted output paths, and whether a full build is required."""
    path = path.replace("\\", "/")
    parts = path.split("/")
    routes = {"/"}

    if len(parts) < 2:
        return routes, set(), False

    if parts[-2] in {"attachments", "media"}:
        source_path = Path(*parts)
        output_prefix = "main" if parts[-2] == "attachments" else "img"
        return routes, {Path("demo") / output_prefix / source_path}, False

    translations_index = parts.index("translations") if "translations" in parts else -1
    if translations_index >= 0:
        language = parts[translations_index + 1] if len(parts) > translations_index + 1 else ""
        content_parts = parts[:translations_index]
        filename = parts[-1]
        if not language or not filename:
            return routes, set(), False
        assignment = "/".join(content_parts + [Path(filename).stem])
        routes.add(f"/main/{assignment}/lang/{language}")
        routes.add(f"/main/{assignment}")
        directory_parts = content_parts
    elif path.endswith((".md", ".oink")):
        directory_parts = parts[:-1]
        assignment = "/".join(directory_parts + [Path(parts[-1]).stem])
        routes.add(f"/main/{assignment}")
    elif path.endswith("meta.json"):
        directory_parts = parts[:-1]
        if directory_parts:
            routes.add(f"/main/{'/'.join(directory_parts)}")
    else:
        return routes, set(), False

    for index in range(1, len(directory_parts) + 1):
        routes.add(f"/main/{'/'.join(directory_parts[:index])}/")

    return routes, set(), False


def _media_link_for_path(path: str) -> str | None:
    parts = path.replace("\\", "/").split("/")
    if len(parts) < 2 or parts[-2] not in {"attachments", "media"}:
        return None
    prefix = "main" if parts[-2] == "attachments" else "img"
    return f"/{prefix}/{'/'.join(parts)}"


def _output_path_for_route(route: str) -> Path:
    if route == "/":
        return Path("demo/index.html")
    path = route.split("#", 1)[0].strip("/")
    if route.endswith("/") and "." not in path:
        path += "/index.html"
    elif "." not in path.rsplit("/", 1)[-1]:
        path += ".html"
    return Path("demo") / path


def configure_demo_build() -> tuple[str, str, bool]:
    """Restore either a full or incremental build based on the cached demo state."""
    global incremental_mode, links, api_links, api_view_links, changed_media_links

    api_view_links.clear()
    changed_media_links.clear()
    root_dir = Path(__file__).resolve().parents[2]
    piggybank_path = root_dir / "piggybank"
    root_revision = _git_revision(root_dir)
    root_worktree_fingerprint = _worktree_fingerprint(root_dir)
    piggybank_revision = _git_revision(piggybank_path)
    piggybank_worktree_fingerprint = _piggybank_worktree_fingerprint(piggybank_path)
    state_path = Path(".demo-state.json")
    previous_state = {}
    if state_path.exists():
        with state_path.open(encoding="utf-8") as file:
            previous_state = json.load(file)

    full_build = (
        os.environ.get("FORCE_FULL_REBUILD", "").lower() == "true"
        or
        not previous_state
        or previous_state.get("root_revision") != root_revision
        or previous_state.get("root_worktree_fingerprint") != root_worktree_fingerprint
        or not previous_state.get("piggybank_revision")
    )
    changes = []
    if not full_build and (
        previous_state["piggybank_revision"] != piggybank_revision
        or previous_state.get("piggybank_worktree_fingerprint") != piggybank_worktree_fingerprint
    ):
        changes = _changed_piggybank_files(
            piggybank_path, previous_state["piggybank_revision"], piggybank_revision
        )

    if full_build:
        rmtree("demo", ignore_errors=True)
        incremental_mode = False
        links = {"/", "/404"}
        api_links = {"/api/search-data"}
    else:
        incremental_mode = True
        if not changes:
            links = set()
            api_links = set()
            api_view_links = set()
            visited.clear()
            media_links.clear()
            return root_revision, piggybank_revision, False
        affected_routes = {"/"}
        deleted_outputs = set()
        for status, path in changes:
            routes, deleted, requires_full_build = _route_for_path(path)
            if requires_full_build:
                rmtree("demo", ignore_errors=True)
                incremental_mode = False
                links = {"/", "/404"}
                api_links = {"/api/search-data"}
                break
            affected_routes.update(routes)
            deleted_outputs.update(deleted)
            if status != "D" and (media_link := _media_link_for_path(path)):
                changed_media_links.add(media_link)
            if status == "D":
                deleted_outputs.update(_output_path_for_route(route) for route in routes)
        else:
            links = affected_routes
            api_links = {"/api/search-data"}
            api_view_links = set()
            for route in affected_routes:
                output_path = _output_path_for_route(route)
                if output_path.exists():
                    output_path.unlink()
            for output_path in deleted_outputs:
                output_path.unlink(missing_ok=True)

    visited.clear()
    media_links.clear()
    return root_revision, piggybank_revision, True


if __name__ == "__main__":
    root_revision, piggybank_revision, build_required = configure_demo_build()
    root_dir = Path(__file__).resolve().parents[2]
    if build_required:
        generate_static_files(static_folder=Path("demo/static").absolute())
        download_site()
        download_api_views()
        # Since we are in .github/workflows, we need to go up two directories to find the piggy folder
        copytree(root_dir / "piggy" / "static", Path("demo/static").absolute(), dirs_exist_ok=True)
        minify_folder(Path("demo/static").absolute())
    else:
        print("No demo changes detected; using cached demo.")
    with Path(".demo-state.json").open("w", encoding="utf-8") as file:
        json.dump(
            {
                "root_revision": root_revision,
                "root_worktree_fingerprint": _worktree_fingerprint(root_dir),
                "piggybank_revision": piggybank_revision,
                "piggybank_worktree_fingerprint": _piggybank_worktree_fingerprint(root_dir / "piggybank"),
            },
            file,
        )
