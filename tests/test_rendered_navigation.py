import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

from bs4 import BeautifulSoup
from turtleconverter import mdfile_to_sections

from piggy.rendered_navigation import repair_rendered_navigation
from piggy.utils import disable_server_side_markdown_exec, normalize_path_to_str


def repair(body):
    return repair_rendered_navigation(
        body,
        route="main",
        normalize_page_path=lambda path: normalize_path_to_str(path, normalize_page_path=True, normalize_url=True),
    )


class RenderedNavigationTests(unittest.TestCase):
    def test_encoded_wiki_section_link_matches_page_route(self):
        body = (
            '<a href="/main/VG2/IT/Driftsstotte/Docker/Docker%20Level%200%20-%20Hva%20er%20Docker.md#ett-image">Les</a>'
        )
        link = BeautifulSoup(repair(body), "html.parser").a
        self.assertEqual(link["href"], "/main/VG2/IT/Driftsstotte/Docker/Docker_Level_0_-_Hva_er_Docker#ett-image")

    def test_norwegian_path_punctuation_and_encoded_fragment(self):
        body = '<a href="/main/Åpen%20mappe/Nivå%201.2,%20-%20Øving.md?lang=nno&amp;x=1#øving%20én">Les</a>'
        self.assertEqual(
            BeautifulSoup(repair(body), "html.parser").a["href"],
            "/main/Åpen_mappe/Nivå_12_-_Øving?lang=nno&x=1#øving%20én",
        )

    def test_plain_markdown_link_uses_same_route(self):
        body = '<a href="/main/VG2/IT/Docker Level 0.md">Les</a>'
        self.assertEqual(BeautifulSoup(repair(body), "html.parser").a["href"], "/main/VG2/IT/Docker_Level_0")

    def test_external_media_and_same_page_links_are_unchanged(self):
        for href in (
            "https://example.com/main/File.md#title",
            "//example.com/main/File.md",
            "https://[invalid",
            "/img/File.md#title",
            "#øving",
            "/main/VG2/File#øving",
            "/main/VG2/attachments/File.pdf",
            "mailto:teacher@example.com",
        ):
            with self.subTest(href=href):
                body = f'<a href="{href}">Les</a>'
                self.assertEqual(repair(body), body)

    def test_stale_converter_skip_link_is_removed_without_losing_content(self):
        body = '<a class="md-skip other" href="#removed-h1">Skip to content</a><h2 id="kept">Behold</h2><p>Tekst</p>'
        soup = BeautifulSoup(repair(body), "html.parser")
        self.assertIsNone(soup.select_one(".md-skip"))
        self.assertEqual(soup.h2["id"], "kept")
        self.assertEqual(soup.p.text, "Tekst")

    def test_code_examples_and_scripts_survive_link_repair(self):
        body = (
            '<a href="/main/File%20one.md#section">Les</a>'
            '<pre><code>&lt;a href="/main/File two.md"&gt;</code></pre>'
            "<script>const sample = \"<a href='/main/File three.md'>\";</script>"
        )
        soup = BeautifulSoup(repair(body), "html.parser")
        self.assertEqual(soup.code.text, '<a href="/main/File two.md">')
        self.assertEqual(soup.script.string, "const sample = \"<a href='/main/File three.md'>\";")

    def test_repeated_repair_has_no_further_changes(self):
        body = '<a class="md-skip" href="#old">Skip</a><a href="/main/File%20one.md#section">Les</a>'
        once = repair(body)
        self.assertEqual(repair(once), once)

    def test_heading_alias_keeps_original_id_and_excludes_permalink(self):
        body = '<h2 id="ving-med-en">Øving med én<a class="headerlink" href="#ving-med-en">¶</a></h2>'
        soup = BeautifulSoup(repair(body), "html.parser")
        self.assertIsNotNone(soup.find(id="ving-med-en"))
        self.assertIsNotNone(soup.find(id="øving-med-én"))
        self.assertEqual(soup.a["href"], "#ving-med-en")
        self.assertEqual(repair(str(soup)), str(soup))

    def test_aliases_do_not_duplicate_explicit_ids_or_repeated_headings(self):
        body = '<div id="øving">Eget anker</div><h2 id="ving">Øving</h2><h2 id="ving_1">Øving</h2>'
        soup = BeautifulSoup(repair(body), "html.parser")
        self.assertEqual(len(soup.find_all(id="øving")), 1)
        self.assertEqual(len(soup.find_all(id="ving_1")), 1)

    def test_actual_converter_section_link_reaches_other_series_heading(self):
        disable_server_side_markdown_exec()
        template = Path(__file__).resolve().parents[1] / "piggy/templates/assignments/tconvert_assignment_base.html"
        with tempfile.TemporaryDirectory() as temp:
            docs = Path(temp)
            source = docs / "VG2/IT/Driftsstotte/Serverinstallasjon/Server Level 1 - Start.md"
            target = docs / "VG2/IT/Driftsstotte/Docker/Docker Level 0 - Hva er Docker.md"
            source.parent.mkdir(parents=True)
            target.parent.mkdir(parents=True)
            source.write_text(
                "---\ntitle: Start\n---\n# Start\n\n[[Docker Level 0 - Hva er Docker#Øving med én container|Gå til øving]]\n",
                encoding="utf-8",
            )
            target.write_text(
                "---\ntitle: Hva er Docker\n---\n# Hva er Docker\n\n## Øving med én container\n\nInnhold.\n",
                encoding="utf-8",
            )
            options = dict(
                docs_folder=docs,
                leading_url="/main",
                normalize_urls=True,
                template=template,
                remove_heading_if_title_matches=True,
            )
            source_body = mdfile_to_sections(source, **options)["body"]
            target_body = mdfile_to_sections(target, **options)["body"]
            link = BeautifulSoup(repair(source_body), "html.parser").find("a", string="Gå til øving")
            target_soup = BeautifulSoup(repair(target_body), "html.parser")
            expected = normalize_path_to_str(
                "/main/" + target.relative_to(docs).with_suffix("").as_posix(),
                normalize_page_path=True,
                normalize_url=True,
            )
            path, fragment = link["href"].split("#", 1)
            self.assertEqual(path, expected)
            self.assertIsNotNone(target_soup.find(id=unquote(fragment)))
            self.assertIsNone(target_soup.h1)
            self.assertIsNone(target_soup.select_one(".md-skip"))


if __name__ == "__main__":
    unittest.main()
