"""Template checks run with the app's normal Jinja dependency installed."""

import unittest
from pathlib import Path
from html.parser import HTMLParser

from jinja2 import Environment, FileSystemLoader

import test_books


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.append(dict(attrs))


class BookTemplatesTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_books.BooksTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.index = self.fixture.build()
        self.env = Environment(
            loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "piggy" / "templates"),
            autoescape=False,  # Match the app; new metadata must be escaped explicitly.
        )

    def render(self, template, **kwargs):
        return self.env.get_template(template).render(**kwargs)

    def render_article(self, navigation):
        from jinja2 import ChoiceLoader, DictLoader

        self.env.loader = ChoiceLoader(
            [
                DictLoader(
                    {
                        "layout.html": "{% block base %}{% endblock %}",
                        "partials/parts/relevant_pages.html": "",
                    }
                ),
                self.env.loader,
            ]
        )
        return self.render(
            "assignments/5-assignment.html",
            book_navigation=navigation,
            content={"heading": "Page", "body": "<p>Page content</p>"},
        )

    def test_all_six_chapters_are_native_links_even_on_contents_page(self):
        rendered = self.render(
            "partials/header/book-navigation.html", book_navigation=self.index[self.fixture.contents]
        )
        parser = Links()
        parser.feed(rendered)
        self.assertEqual(len(parser.links), 7)
        self.assertEqual(parser.links[0]["aria-current"], "location")
        self.assertEqual(
            [link["href"].rsplit("#", 1)[-1] for link in parser.links[1:]], [f"kapittel-{i}" for i in range(1, 7)]
        )
        self.assertNotIn("Kapittel 0", rendered)

    def test_shared_page_has_two_clickable_chapters_and_only_one_current(self):
        rendered = self.render(
            "partials/header/book-navigation.html", book_navigation=self.index[self.fixture.protocols[0]]
        )
        parser = Links()
        parser.feed(rendered)
        self.assertEqual(sum("aria-current" in link for link in parser.links), 1)
        self.assertEqual(sum("data-book-local" in link for link in parser.links), 2)
        self.assertTrue(parser.links[3]["href"].endswith("#kapittel-3"))

    def test_title_markup_is_escaped_with_autoescape_disabled(self):
        navigation = self.index[self.fixture.protocols[0]]
        navigation["title"] = '<img src=x onerror="bad()"> & switches'
        navigation["chapters"][1]["label"] = '<svg onload="bad()">'
        rendered = self.render("partials/header/book-navigation.html", book_navigation=navigation)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("<svg", rendered)
        self.assertIn("&lt;img", rendered)
        self.assertIn("&lt;svg", rendered)
        self.assertIn("&amp; switches", rendered)

    def test_header_uses_legacy_selector_for_nonmembers(self):
        template = self.env.get_template("partials/header/navigation.html")
        # Stub includes so this checks only the routing decision, independently
        # of old/new app differences in unrelated header controls.
        from jinja2 import ChoiceLoader, DictLoader

        self.env.loader = ChoiceLoader(
            [
                DictLoader(
                    {
                        "partials/header/logo.html": "",
                        "partials/header/back-button.html": "",
                        "partials/header/level-selector.html": "LEGACY_SELECTOR",
                        "partials/header/book-navigation.html": "BOOK_SELECTOR",
                        "partials/parts/settings/search-button.html": "",
                        "partials/header/language-selector.html": "",
                        "partials/parts/settings.html": "",
                        "partials/parts/shortlink_copy.html": "",
                    }
                ),
                self.env.loader,
            ]
        )
        context = {"current_language": {}, "supported_languages": {}, "url_for": lambda *args, **kwargs: "asset.js"}
        legacy = template.render(**context)
        self.assertIn("LEGACY_SELECTOR", legacy)
        self.assertNotIn("BOOK_SELECTOR", legacy)
        book = template.render(**context, book_navigation=self.index[self.fixture.contents])
        self.assertIn("BOOK_SELECTOR", book)
        self.assertNotIn("LEGACY_SELECTOR", book)

    def test_heading_and_both_pagination_copies_escape_metadata(self):
        navigation = self.index[self.fixture.protocols[0]]
        navigation["title"] = '<img src=x onerror="bad()">'
        navigation["previous"]["label"] = "<script>bad()</script>"
        navigation["next"]["label"] = "<svg onload=bad()>"
        rendered = self.render_article(navigation)
        self.assertEqual(rendered.count("data-book-previous-label"), 2)
        self.assertEqual(rendered.count("data-book-next-label"), 2)
        self.assertIn("Forrige:", rendered)
        self.assertIn("Neste:", rendered)
        for tag in ("img", "script", "svg"):
            self.assertNotIn(f"<{tag}", rendered)
            self.assertIn(f"&lt;{tag}", rendered)

    def test_contents_article_has_six_visible_native_chapter_links(self):
        rendered = self.render_article(self.index[self.fixture.contents])
        self.assertIn('class="book-contents"', rendered)
        parser = Links()
        parser.feed(rendered)
        chapter_links = [link for link in parser.links if "#kapittel-" in link.get("href", "")]
        for number in range(1, 7):
            self.assertTrue(any(link["href"].endswith(f"#kapittel-{number}") for link in chapter_links))
        self.assertNotIn('class="book-contents"', self.render_article(self.index[self.fixture.protocols[0]]))


if __name__ == "__main__":
    unittest.main()
