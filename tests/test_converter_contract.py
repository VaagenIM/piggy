"""Test converter output directly, without reparsing or repairing it in Piggy."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from piggy import caching
from piggy.utils import disable_server_side_markdown_exec, normalize_path_to_str


class ConverterContractTests(unittest.TestCase):
    def render(self, docs, name, text):
        path = docs / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        disable_server_side_markdown_exec()
        with patch.object(caching, "PIGGYBANK_FOLDER", docs):
            return caching._mdfile_to_sections_with_retry(path)["body"]

    def test_title_and_native_skip_target_survive_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = self.render(
                Path(tmp), "Test Level 1 - Start.md", "---\ntitle: Start\n---\n# Start!\n\n## Øving\n\nFagtekst.\n"
            )
        soup = BeautifulSoup(body, "html.parser")
        self.assertEqual(len(soup.find_all("h1")), 1)
        skip = soup.select_one("a.md-skip")
        self.assertIsNotNone(skip)
        self.assertIsNotNone(soup.find(id=skip["href"].removeprefix("#")))
        self.assertIn("Fagtekst.", soup.get_text())

    def test_title_removed_if_matching_frontmatter(self):
        # Since the title is the same as the first heading, it should be removed from the body (the template will render it in a separate <h1>).
        with tempfile.TemporaryDirectory() as tmp:
            body = self.render(
                Path(tmp), "Test Level 1 - Start.md", "---\ntitle: Start\n---\n# Start\n\n## Øving\n\nFagtekst.\n"
            )
        soup = BeautifulSoup(body, "html.parser")
        self.assertEqual(len(soup.find_all("h1")), 0)
        self.assertIn("Fagtekst.", soup.get_text())

    def test_canonical_section_link_reaches_native_heading(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            target_name = "VG2/IT/Docker/Docker Level 0 - Start.md"
            target_body = self.render(
                docs, target_name, "---\ntitle: Start\n---\n# Start\n\n## Øving med én\n\nPrøv.\n"
            )
            target = BeautifulSoup(target_body, "html.parser")
            fragment = target.h2["id"]
            route = normalize_path_to_str(
                "/main/" + str(Path(target_name).with_suffix("")), normalize_page_path=True, normalize_url=True
            )
            url = "https://piggy.iktim.no" + route + "#" + fragment
            body = self.render(docs, "VG2/IT/Test/Test Level 1 - Les.md", f"---\ntitle: Les\n---\n[Øv]({url})\n")
        link = BeautifulSoup(body, "html.parser").find("a", string="Øv")
        self.assertEqual(link["href"], url)
        self.assertIsNotNone(target.find(id=fragment))

    def test_explicit_compatibility_anchor_preserves_old_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = self.render(
                Path(tmp),
                "Test Level 1 - Lister.md",
                '---\ntitle: Lister\n---\n[Oppgave](#oppgave-1---lister)\n\n## Oppgave 1 - Lister\n\n<span id="oppgave-1---lister"></span>\n\nLag en liste.\n',
            )
        soup = BeautifulSoup(body, "html.parser")
        self.assertIsNotNone(soup.find(id="oppgave-1-lister"))
        self.assertEqual(len(soup.find_all(id="oppgave-1---lister")), 1)

    def test_code_fences_and_interactive_embed_are_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            docs = Path(tmp)
            sentinel = docs / "executed.txt"
            text = f"""---
title: Kode
---
```html
<a href="File.md#øving">Eksempel</a>
```
```jinja
{{{{ navn }}}}
```
```mermaid
graph LR; A-->B;
```
```python exec
from pathlib import Path
Path({str(sentinel)!r}).write_text("should not execute")
```
<iframe src="attachments/test.html" title="Selvtest"></iframe>
"""
            body = self.render(docs, "Test Level 1 - Kode.md", text)
            self.assertFalse(sentinel.exists())
        soup = BeautifulSoup(body, "html.parser")
        self.assertIn('<a href="File.md#øving">Eksempel</a>', soup.get_text())
        self.assertIn("{{ navn }}", soup.get_text())
        self.assertIn("graph LR; A-->B;", soup.get_text())
        self.assertEqual(soup.iframe["src"], "attachments/test.html")
        self.assertEqual(soup.iframe["title"], "Selvtest")


if __name__ == "__main__":
    unittest.main()
