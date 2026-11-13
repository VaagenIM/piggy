"""
Builds the static GitHub Pages version of the site from a running piggy server (GITHUB_PAGES=1).

The server lists every page up front (/sitemap-internal) and every media/attachments file (/sitemap-internal/files),
so all pages are fetched in a single pass and the files are copied straight from disk. Only media that doesn't exist
as a file (generated fallback thumbnails, placeholders) is downloaded from the server.
"""

import multiprocessing
import os
import posixpath
import re
import time
from pathlib import Path
from shutil import copyfile, copytree, rmtree
from urllib.parse import unquote, urlunsplit, urlsplit

import htmlmin
import requests
from bs4 import BeautifulSoup as bs
from rcssmin import cssmin
from rjsmin import jsmin

WORKERS = max(1, multiprocessing.cpu_count() - 1)

url = "http://127.0.0.1:55555"  # The URL of the website we are scraping
cname = "https://piggy.iktim.no"  # The CNAME of the website we will push the demo to

# Pages that aren't in the sitemap, and the API endpoints the site fetches itself
extra_pages = {"/404", "/sitemap.xml"}
api_links = {"/api/search-data", "/api"}

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
root_dir = Path(__file__).resolve().parents[2]


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
            # if we are trying to visit "404", we don't want to retry, as it will always fail
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
                f"WARNING: Could not fetch {url_to_fetch} after "
                f"{max_attempts} attempts (status code: {response.status_code})"
            )
            return response

        if url_to_fetch.endswith("/404"):
            print(
                f"WARNING: Could not fetch {url_to_fetch} "
                f"(status code: {response.status_code}). "
                "Not retrying, as this is the 404 page."
            )
            return response

        print(
            f"WARNING: Could not fetch {url_to_fetch} "
            f"(status code: {response.status_code}). "
            f"Retrying attempt {attempt + 1}/{max_attempts}..."
        )
        time.sleep(attempt)

    return last_response


def get_internal_sitemap() -> set[str]:
    """Return all page paths (including pages not linked from public navigation) and their shortlinks."""
    response = get_with_retry(f"{url}/sitemap-internal")
    response.raise_for_status()
    return {line.strip() for line in response.text.splitlines() if line.strip()}


def get_internal_files() -> list[tuple[str, Path]]:
    """Return (url path, file on disk) pairs for every media and attachments file."""
    response = get_with_retry(f"{url}/sitemap-internal/files")
    response.raise_for_status()
    return [(path, Path(file)) for path, file in (line.split("\t", 1) for line in response.text.splitlines() if line)]


def clean_link(link, path):
    link = link.replace("&amp;", "&").replace(" ", "_")

    # Separate path/query/fragment so query parameters are preserved
    parsed = urlsplit(link)
    link_path = unquote(parsed.path)

    if re.match(r"\.?.+[#:].*", link_path.split("/")[-1]) and path:
        # Reconstruct without #.* or :.* in the filename.
        stem = link_path.split("/")[-1].split("#")[0].split(":")[0]
        directories = link_path.split("/")[:-1]
        link_path = "/".join(directories + [stem])

    # Add path to relative links
    if not link_path.startswith("/") and path:
        link_path = f"/{path.rsplit('/', 1)[0]}/{link_path}"

    # Replace \\ with /
    link_path = link_path.replace("\\", "/")

    # Resolve relative path segments while preserving query + fragment.
    if link_path:
        link_path = posixpath.normpath(link_path)

    return urlunsplit(("", "", link_path, parsed.query, parsed.fragment))


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
        filtered_links.add(link)

    return filtered_links


def output_path_for_route(route: str) -> Path:
    """Return the file a page route is written to, <route>.html unless the route has a file extension."""
    path = route.split("?", 1)[0].split("#", 1)[0].strip("/")
    if not path:
        return Path("demo/index.html")
    if "." not in path.rsplit("/", 1)[-1]:
        path += ".html"
    return Path("demo") / path


def output_path_for_media(link: str) -> Path:
    """Return the file a media link is written to (without its query string or fragment)."""
    path = unquote_path(link.strip("/").split("#", 1)[0].split("?", 1)[0])
    # TODO: this is a hack. hopefully temporary.
    if "/api/generate_thumbnail/" in link:
        path += ".webp"
    return Path("demo") / path


def process_html(html: str, link: str) -> str:
    """Rewrite a fetched page for its static location."""
    # TODO: this is a hack. hopefully temporary.
    html = re.sub(
        r"""/api/generate_thumbnail/([^?"]*)(\?[^"]*)?""",
        lambda m: (
            f"/api/generate_thumbnail/{re.sub(r'[^A-Za-z0-9_]', '', clean_link(m.group(1), path=''))}.webp{m.group(2) or ''}"
        ),
        html,
    )
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
            rf"""href=\"({link.split("Level")[0].split("/")[-1]}[^/]+)\"""",
            rf'href="../../\1/lang/{lang}"',
            html,
        )
    return html


def write_html(html: str, output_path: Path):
    if output_path != Path("demo/sitemap.xml"):
        html = htmlmin.minify(
            html,
            remove_comments=True,
            remove_empty_space=True,
            reduce_boolean_attributes=True,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        f.write(html.encode())


def build_page(link: str) -> tuple[str, bool, set[str]]:
    """Fetch, rewrite and write one page, returning whether it worked and the media it links to."""
    page_url = f"{url}/{link.strip('/')}"
    r = get_with_retry(page_url)

    if not r.ok and link != "/404":
        if link == "/":
            raise Exception("Could not fetch the main page. Is the server running?")
        print(f"WARNING: Could not fetch {link} (status code: {r.status_code})")
        return link, False, set()

    # Normalize html (quoted attributes etc.) so the regexes below match
    is_html = "text/html" in r.headers.get("Content-Type", "")
    html = str(bs(r.text, "html.parser")) if is_html else r.text

    # Translations share the media of the page they translate
    media_links = get_media_links(html, path=link.strip("/")) if "/lang/" not in link else set()

    write_html(process_html(html, link), output_path_for_route(link))
    return link, True, media_links


def copy_file(path: str, file: Path):
    output_path = output_path_for_media(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    copyfile(file, output_path)


def download_media(link: str):
    # The URL used for downloading keeps the query string.
    request_path = link.strip("/").split("#", 1)[0]
    output_path = output_path_for_media(link)

    if output_path == Path("demo"):
        print(f"WARNING: Could not download {link}: empty output path")
        return
    if len(output_path.name) > 255:
        print("WARNING: Cannot download file with name longer than 255 characters")
        return

    try:
        r = requests.get(f"{url}/{request_path}", allow_redirects=True, timeout=600)
    except requests.RequestException as e:
        print(f"WARNING: Could not download {link}: {e}")
        return

    if not r.ok:
        print(f"WARNING: Could not download {link} (status code: {r.status_code})")
        return

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("wb") as f:
            f.write(r.content)
    except Exception as e:
        print(f"WARNING: Could not write file {output_path}: {e}")


def is_api_view_link(link: str) -> bool:
    """Return whether a successfully fetched page should have a static API view."""
    path = link.split("?", 1)[0].split("#", 1)[0].strip("/")
    if not path.startswith("main/"):
        return False
    return not any(segment in path.split("/") for segment in ("lang", "attachments", "media"))


def api_transform(link: str) -> str:
    """Return the API path of a page, /main/<path> becomes /api/<path>."""
    link = link.split("?")[0].split("#")[0].strip("/")
    link = link[len("main/") :]
    # remove file extensions
    link = re.sub(r"\.[a-zA-Z0-9]+$", "", link)
    return f"/api/{link}"


def download_api(api_path: str):
    """Download an /api/ path, saving it as index.json under demo/."""
    try:
        r = requests.get(f"{url}{api_path}", timeout=600)
    except Exception as e:
        print(f"WARNING: request failed for {api_path}: {e}")
        return
    if not r.ok:
        print(f"WARNING: failed {api_path} ({r.status_code})")
        return
    full_path = Path(f"demo{api_path}") / "index.json"
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(r.content)


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


def timed(step: str, started: float):
    print(f"\33[32m{step} in {time.perf_counter() - started:.1f}s\33[0m")
    return time.perf_counter()


def build_site():
    # Imported here, so pool workers started with spawn (Windows, macOS) don't each set up mkdocs
    from turtleconverter import generate_static_files

    started = time.perf_counter()
    rmtree("demo", ignore_errors=True)
    generate_static_files(static_folder=Path("demo/static").absolute())

    pages = sorted(get_internal_sitemap() | extra_pages)
    files = get_internal_files()
    started = timed(f"Listed {len(pages)} pages and {len(files)} files", started)

    with multiprocessing.Pool(processes=WORKERS) as pool:
        pool.starmap(copy_file, files)
        started = timed(f"Copied {len(files)} files", started)

        built, media_links = [], set()
        for link, ok, links in pool.imap_unordered(build_page, pages, chunksize=4):
            print(f"{'Built' if ok else 'Skipped'} \33[34m{link}\33[0m")
            if ok:
                built.append(link)
            media_links |= links
        started = timed(f"Built {len(built)}/{len(pages)} pages", started)

        # Media that isn't a file on disk is generated by the server (e.g. fallback thumbnails). Links that only
        # differ in their query string (?title=) share one file, so only the first of them is downloaded
        missing = {}
        for link in sorted(media_links):
            if not output_path_for_media(link).exists():
                missing.setdefault(output_path_for_media(link), link)
        pool.map(download_media, missing.values())
        started = timed(f"Downloaded {len(missing)} generated media files", started)

        api_paths = sorted({api_transform(link) for link in built if is_api_view_link(link)} | api_links)
        pool.map(download_api, api_paths)
        started = timed(f"Downloaded {len(api_paths)} API views", started)

    copytree(root_dir / "piggy" / "static", Path("demo/static").absolute(), dirs_exist_ok=True)
    minify_folder(Path("demo/static").absolute())
    timed("Copied and minified static files", started)


if __name__ == "__main__":
    build_site()
