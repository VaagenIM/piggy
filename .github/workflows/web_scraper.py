"""
A hacky script that scrapes a website and downloads all the pages and media files.
"""

import shutil
import requests
import re
import os
from turtleconverter import generate_static_files
from pathlib import Path

links = ["/"]  # A list of links we need to visit and download (including files that are related to the website)
visited = []  # A list of links we have visited
media_links = []
url = "http://localhost:5000"  # The URL of the website we are scraping

os.chdir(os.path.dirname(os.path.abspath(__file__)))


def get_html(link):
    """Get the html from the given url, and append the new links to the links list."""
    r = requests.get(f'{url}/{link.strip("/")}', allow_redirects=True)
    html = r.text
    new_links = get_links(html)
    new_media_links = get_media_links(html)

    for l in new_links:
        if l not in links:
            links.append(l)

    for l in new_media_links:
        if l not in media_links:
            media_links.append(l)

    visited.append(link)
    return html


def get_links(html):
    links = re.compile(r'href="(\/[^"]*)"').findall(html)
    return list(set([x for x in links if not re.match(r"/static/.*", x)]))


def get_media_links(html):
    links = re.compile(r'src="((?!https?://)[^"]*)"').findall(html)
    return list(set([x for x in links if not re.match(r"/static/.*", x)]))


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

                os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
                with open(f"demo/{path}", "w+", encoding="utf-8") as f:
                    f.write(html)
    for link in media_links:
        path = link.strip("/")
        r = requests.get(f"{url}/{path}", allow_redirects=True)
        os.makedirs(os.path.dirname(f"demo/{path}"), exist_ok=True)
        with open(f"demo/{path}", "wb") as f:
            f.write(r.content)


shutil.copytree(Path(__file__).parents[2] / "piggy/static", Path("demo/static"))
generate_static_files(static_folder=Path("demo/static").absolute())
download_site()
