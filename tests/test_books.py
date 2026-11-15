import tempfile
import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from piggy.books import BookValidationError, build_book_index


class BookIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        (self.root / "Innhold.md").write_text("# Innhold\n", encoding="utf-8")
        (self.root / "Introduksjon.md").write_text(
            '<a id="intro"></a>\n# Introduksjon\n',
            encoding="utf-8",
        )

    def make_piggymap(self, *, chapter_visibility="public", include_anchor=True):
        chapter = self.root / "Introduksjon.md"
        if not include_anchor:
            chapter.write_text("# Introduksjon\n", encoding="utf-8")
        return {
            "VG1": {
                "data": {
                    "1IM": {
                        "data": {
                            "Fag": {
                                "data": {
                                    "Grunnbok": {
                            "meta": {
                                "book": {
                                    "title": "Grunnbok",
                                    "contents": "Innhold.md",
                                    "chapters": [
                                        {
                                            "title": "Introduksjon",
                                            "page": "Introduksjon.md",
                                            "anchor": "intro",
                                        }
                                    ],
                                }
                            },
                            "data": {
                                "Innhold": {
                                    "path": str(self.root / "Innhold.md"),
                                    "meta": {"visibility": "public"},
                                    "translation_meta": {
                                        "eng": {"title": "Contents &amp; overview"},
                                    },
                                },
                                "Introduksjon": {
                                    "path": str(chapter),
                                    "meta": {"visibility": chapter_visibility},
                                    "translation_meta": {
                                        "eng": {"title": "Getting &amp; started"},
                                    },
                                },
                            },
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

    def test_builds_translated_labels_and_language_urls(self):
        index = build_book_index(self.make_piggymap(), self.root)
        navigation = index["Introduksjon.md"]

        self.assertEqual(navigation["language_titles"], {"eng": "Contents & overview"})
        self.assertEqual(navigation["current"]["language_labels"], {"eng": "1. Getting & started"})
        self.assertEqual(
            navigation["current"]["language_urls"]["eng"],
            "/main/VG1/1IM/Fag/Grunnbok/Introduksjon/lang/eng#intro",
        )
        self.assertEqual(navigation["current"]["label"], "Kapittel 1 – Introduksjon")

    def test_rejects_missing_chapter_anchor(self):
        with self.assertRaisesRegex(BookValidationError, "expected exactly one explicit"):
            build_book_index(self.make_piggymap(include_anchor=False), self.root)

    def test_rejects_nonpublic_book_page(self):
        with self.assertRaisesRegex(BookValidationError, "page is not a public assignment"):
            build_book_index(self.make_piggymap(chapter_visibility="unlisted"), self.root)

    def test_book_menu_uses_translated_and_escaped_labels(self):
        index = build_book_index(self.make_piggymap(), self.root)
        template_root = Path(__file__).parents[1] / "piggy" / "templates"
        environment = Environment(loader=FileSystemLoader(template_root), autoescape=False)
        rendered = environment.get_template("partials/header/book-navigation.html").render(
            book_navigation=index["Introduksjon.md"],
            current_language={"key": "eng"},
            github_pages=True,
        )

        self.assertIn("Contents &amp; overview", rendered)
        self.assertIn("1. Getting &amp; started", rendered)
        self.assertIn("/main/VG1/1IM/Fag/Grunnbok/Introduksjon/lang/eng#intro", rendered)


if __name__ == "__main__":
    unittest.main()
