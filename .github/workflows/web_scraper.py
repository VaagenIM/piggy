"""
A hacky script that scrapes a website and downloads all the pages and media files.
"""

import os
import re
import shutil
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup as bs
from turtleconverter import generate_static_files

links = ["/"]  # A list of links we need to visit and download (including files that are related to the website)
visited = []  # A list of links we have visited
media_links = []
url = "http://localhost:5000"  # The URL of the website we are scraping
cname = "https://piggy.iktim.no"  # The CNAME of the website we will push the demo to

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_html(link):
    """Get the html from the given url, and append the new links to the links list."""
    print(f"Visiting {url}/{link.strip('/')}")
    r = requests.get(f'{url}/{link.strip("/")}', allow_redirects=True)

    # Only prettify if mimetype is text/html
    if "text/html" in r.headers.get("Content-Type"):
        html = str(bs(r.text, "html.parser"))
    else:
        html = r.text

    new_links = get_links(html, path=link.strip("/"))

    for l in new_links:
        if l not in links:
            links.append(l)

    # Get media links as long as we are not in the lang folder
    if "/lang/" not in link:
        new_media_links = get_media_links(html, path=link.strip("/"))
        for l in new_media_links:
            if l not in media_links:
                media_links.append(l)

    visited.append(link)

    # TODO: this is a hack. hopefully temporary.
    html = re.sub(r"""/api/generate_thumbnail/([^?]*)(\?[^"]*)""", r"/api/generate_thumbnail/\1.webp", html)

    # Replace all content (og) links with the cname
    html = re.sub(rf"content=\"({url})([^\"/]*)", rf'content="{cname}\2', html)

    # A hack to fix media links
    if "/lang/" in link:
        html = re.sub(r'href="attachments/', 'href="../../attachments/', html)
        html = re.sub(r'src="attachments/', 'src="../../attachments/', html)

    return html


def get_links(html, path=""):
    links = re.compile(r'href="((?!#|https?://)[^"]*)"').findall(html)
    filtered_links = list()
    for link in links:
        if not link.startswith("/") and path:
            filtered_links.append(f"{path.rsplit('/', 1)[0]}/{link}")
            continue
        filtered_links.append(link)
    return list(set([x for x in filtered_links]))


def get_media_links(html, path=""):
    links = re.compile(r'src="((?!#|https?://)[^"]*)"').findall(html)
    filtered_links = list()
    for link in links:
        if not link.startswith("/") and path:
            filtered_links.append(f"{path.rsplit('/', 1)[0]}/{link}")
            continue
        filtered_links.append(link)
    return list(set([x for x in filtered_links if not re.match(r"/static/.*", x)]))


def download_site():
    while visited != links:
        for link in links:
            if link not in visited:
                html = get_html(link)
                if link == "/":
                    path = "index.html"
                else:
                    path = link.strip("/")
                    if "." not in path:
                        path += ".html"
                print(f"Writing {link}")
                os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
                with open(f"demo/{path}", "wb+") as f:
                    f.write(html.encode())
    for link in media_links:
        print(f"Downloading {link}")
        path = link.strip("/")
        r = requests.get(f"{url}/{path}", allow_redirects=True)
        os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
        path = unquote(path)
        # TODO: this is a hack. hopefully temporary.
        if "/api/generate_thumbnail/" in link:
            path = path.rsplit("?")[0] + ".webp"

        if not path:
            continue
        with open(f"demo/{path}", "wb+") as f:
            f.write(r.content)


generate_static_files(static_folder=Path("demo/static").absolute())
download_site()
shutil.copytree(Path(__file__).parents[2] / "piggy/static", Path("demo/static"), dirs_exist_ok=True)
