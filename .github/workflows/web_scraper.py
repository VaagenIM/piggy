"""
A hacky script that scrapes a website and downloads all the pages and media files.
"""

import multiprocessing
import os
import re
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup as bs
from turtleconverter import generate_static_files

links = set("/", "/404")  # A list of links we need to visit and download (including files that are related to the website)
visited = set()  # A list of links we have visited
media_links = set()
url = "http://127.0.0.1:5000"  # The URL of the website we are scraping
cname = "https://piggy.iktim.no"  # The CNAME of the website we will push the demo to

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def unquote_path(path):
    new_path = unquote(path)
    new_path = new_path.replace("&amp;", "&")
    return new_path


def get_html(link) -> tuple[str, set[str], set[str]]:
    """Get the html from the given url, and append the new links to the links list."""
    print(f"Visiting \33[34m{url}/{link.strip('/')}\33[0m")
    r = requests.get(f"{url}/{link.strip('/')}", allow_redirects=True)

    visited.add(link)

    if not r.ok:
        return "", set(), set()

    # Only prettify if mimetype is text/html
    if "text/html" in r.headers.get("Content-Type"):
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

    # Replace all content (og) links with the cname
    html = re.sub(rf"content=\"({url})([^\"/]*)", rf'content="{cname}\2', html)

    # A hack to fix media links
    if "/lang/" in link:
        lang = link.split("/lang/")[1].split("/")[0]
        html = re.sub(r'href="attachments/', 'href="../../attachments/', html)
        html = re.sub(r'src="attachments/', 'src="../../attachments/', html)
        html = re.sub(
            rf"""href=\"({link.split("Level")[0].split("/")[-1]}[^/]+)\"""", rf'href="../../\1/lang/{lang}"', html
        )

    # Remove links that are media links
    new_links -= new_media_links
    return html, new_links, new_media_links


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
        link = clean_link(link, path)
        filtered_links.add(link)
    return filtered_links


def get_media_links(html, path=""):
    links = re.compile(r'src="((?!#|https?://)[^"]*)"').findall(html)
    filtered_links = set()
    for link in links:
        link = clean_link(link, path)
        if not link.startswith("/") and path:
            filtered_links.add(f"{path.rsplit('/', 1)[0]}/{link}")
            continue
        filtered_links.add(link)

    return filtered_links


def _write_html(html, path):
    os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
    with open(f"demo/{path}", "wb+") as f:
        f.write(html.encode())


def _download_media(link):
    print(f"Downloading \33[34m{link}\33[0m")
    path = link.strip("/").split("#")[0]
    r = requests.get(f"{url}/{path}", allow_redirects=True)
    os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
    path = unquote_path(path)
    # TODO: this is a hack. hopefully temporary.
    if "/api/generate_thumbnail/" in link:
        path = path.rsplit("?")[0] + ".webp"

    if not path or not r.ok:
        print(f"WARNING: Could not download {link}")
        return

    if len(path.split("/")[-1]) > 255:
        print("WARNING: Cannot download file with name longer than 255 characters")
        return

    with open(f"demo/{path}", "wb+") as f:
        f.write(r.content)


def download_site():
    media_tasks = set()
    tasks = set()
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        while visited != links:
            tasks = set(link for link in links if link not in visited)

            for link in tasks:
                visited.add(link)  # Mark as visited BEFORE calling get_html()

            results = pool.map(get_html, tasks)

            for link, (html, new_links, new_media_links) in zip(tasks, results):
                if html:
                    if link == "/":
                        path = "index.html"
                    else:
                        path = link.strip("/").split("#")[0]
                        if "." not in path:
                            path += ".html"

                    print(f"Writing \33[34m{link}\33[0m")
                    pool.apply_async(_write_html, args=(html, path))  # Run in parallel

                    links.update(new_links)
                    media_tasks.update(new_media_links)
    # A separate pool for media tasks, as we don't want to download multiple media files at once
    # (this appears to happen when we download the media files in parallel with the html files)
    with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
        pool.map(_download_media, media_tasks)  # Download media in parallel


if __name__ == "__main__":
    generate_static_files(static_folder=Path("demo/static").absolute())
    download_site()
