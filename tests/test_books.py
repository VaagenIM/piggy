"""Run without app dependencies: python3 -m unittest discover -s tests -p 'test_books.py'."""

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("piggy_books", APP_ROOT / "piggy" / "books.py")
books = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(books)


class BooksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.topic = {"meta": {}, "data": {}}
        architecture = {"meta": {}, "data": {}}
        self.map = {
            "VG2": {
                "data": {
                    "IT": {
                        "data": {
                            "Drift": {
                                "data": {
                                    "Nettverk": self.topic,
                                    "Arkitektur": architecture,
                                }
                            }
                        }
                    }
                }
            }
        }
        self.contents = "VG2/IT/Drift/Nettverk/Page Level 0 - Innhold.md"
        self.architecture = "VG2/IT/Drift/Arkitektur/Page Level 1 - Arkitektur.md"
        self.protocols = [f"VG2/IT/Drift/Nettverk/Page Level {i} - Protokoller.md" for i in (1, 3, 2)]
        for page in [self.contents, self.architecture, *self.protocols]:
            target = self.root / page
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("# A page\n", encoding="utf-8")
            node = architecture if page == self.architecture else self.topic
            node["data"][target.stem.replace(" ", "_")] = {"path": target, "meta": {"visibility": "public"}}
        chapter_pages = [
            self.architecture,
            self.protocols[0],
            self.protocols[0],
            self.protocols[1],
            self.protocols[1],
            self.protocols[2],
        ]
        chapters = []
        for number, page in enumerate(chapter_pages, 1):
            with (self.root / page).open("a", encoding="utf-8") as file:
                file.write(f'<a id="kapittel-{number}"></a>\n## Topic {number}\n')
            chapters.append({"title": f"Topic {number}", "page": page, "anchor": f"kapittel-{number}"})
        self.book = {"title": "Networking", "contents": self.contents, "chapters": chapters}
        self.topic["meta"]["book"] = self.book

    def build(self):
        return books.build_book_index(self.map, self.root)

    def assertInvalid(self, message):
        with self.assertRaisesRegex(books.BookValidationError, message):
            self.build()

    def test_six_ordered_chapters_on_four_pages_across_topics(self):
        index = self.build()
        self.assertEqual(len(index), 5)
        navigation = index[self.protocols[0]]
        self.assertEqual(navigation["current_indexes"], [2, 3])
        self.assertEqual(navigation["current"]["number"], 2)
        self.assertEqual([c["number"] for c in navigation["chapters"]], list(range(1, 7)))
        self.assertEqual(
            navigation["chapters"][0]["url"], "/main/VG2/IT/Drift/Arkitektur/Page_Level_1_-_Arkitektur#kapittel-1"
        )
        self.assertEqual(navigation["chapters"][2]["url"].split("#")[0], navigation["chapters"][1]["url"].split("#")[0])
        self.assertNotEqual(navigation["chapters"][2]["url"], navigation["chapters"][1]["url"])
        self.assertEqual(navigation["previous"]["number"], 1)
        self.assertEqual(navigation["next"]["number"], 3)
        self.assertIsNone(index[self.contents]["previous"])
        self.assertEqual(index[self.contents]["current"]["label"], "Innhold")
        self.assertNotIn("number", index[self.contents]["current"])
        self.assertIsNone(index[self.protocols[2]]["next"])

    def test_legacy_without_book_is_unchanged(self):
        self.topic["meta"].pop("book")
        self.assertEqual(self.build(), {})

    def test_metadata_is_not_mutated(self):
        before = copy.deepcopy(self.book)
        self.build()
        self.assertEqual(self.book, before)

    def test_invalid_shapes_are_not_silently_hidden(self):
        for value in (
            None,
            {},
            "Networking",
            {**self.book, "chapters": []},
            {**self.book, "title": ""},
            {**self.book, "chapter": []},
        ):
            with self.subTest(value=value):
                self.topic["meta"]["book"] = value
                self.assertInvalid("expected")

    def test_duplicate_targets_and_membership_are_rejected(self):
        self.book["chapters"].append(dict(self.book["chapters"][0]))
        self.assertInvalid("duplicate chapter target")
        self.book["chapters"].pop()
        self.map["VG2"]["data"]["IT"]["data"]["Drift"]["data"]["Arkitektur"]["meta"]["book"] = copy.deepcopy(self.book)
        self.assertInvalid("already belongs to another book")

    def test_missing_and_non_assignment_targets(self):
        (self.root / self.protocols[0]).unlink()
        self.assertInvalid("missing or unsafe")
        (self.root / self.protocols[0]).write_text("# A page")
        self.topic["data"].pop(Path(self.protocols[0]).stem.replace(" ", "_"))
        self.assertInvalid("not a public assignment")

    def test_private_unlisted_and_inherited_visibility_are_rejected(self):
        for visibility in ("private", "unlisted"):
            with self.subTest(visibility=visibility):
                self.topic["data"][Path(self.protocols[0]).stem.replace(" ", "_")]["meta"]["visibility"] = visibility
                self.assertInvalid("not a public assignment")
        self.topic["data"][Path(self.protocols[0]).stem.replace(" ", "_")]["meta"]["visibility"] = "public"
        self.map["VG2"]["meta"] = {"visibility": "private"}
        self.assertInvalid("book owner must be public")

    def test_missing_duplicate_and_fenced_anchor_targets(self):
        target = self.root / self.architecture
        for source in (
            "# Missing",
            '<a id="kapittel-1"></a>\n<a id="kapittel-1"></a>',
            '```html\n<a id="kapittel-1"></a>\n```',
            '    <a id="kapittel-1"></a>',
        ):
            with self.subTest(source=source):
                target.write_text(source, encoding="utf-8")
                self.assertInvalid("exactly one explicit")
        target.write_text("<!-- <a id='kapittel-1'></a> -->\n<a id='kapittel-1'></a>")
        self.build()

    def test_unsafe_paths_and_anchor_urls(self):
        original = self.book["chapters"][0]["page"]
        for value in (
            "../secret.md",
            "/etc/passwd.md",
            "https://example.com/a.md",
            "//evil/a.md",
            "C:/a.md",
            "a%2fb.md",
            "a.md#part",
            "a.md?q=1",
            "a\\b.md",
            "a/./b.md",
            "a//b.md",
            "a\n.md",
        ):
            with self.subTest(value=value):
                self.book["chapters"][0]["page"] = value
                self.assertInvalid("safe root-relative")
        self.book["chapters"][0]["page"] = original
        for value in ("#chapter", "javascript:foo", 'a" onclick="alert(1)', "a b"):
            with self.subTest(value=value):
                self.book["chapters"][0]["anchor"] = value
                self.assertInvalid("safe HTML id")

    def test_symlink_outside_root_is_rejected(self):
        target = self.root / self.architecture
        target.unlink()
        with tempfile.TemporaryDirectory() as outside:
            other = Path(outside) / "page.md"
            other.write_text('<a id="kapittel-1"></a>')
            target.symlink_to(other)
            self.assertInvalid("missing or unsafe")

    def test_routes_use_existing_map_keys(self):
        node = self.topic["data"].pop(Path(self.protocols[0]).stem.replace(" ", "_"))
        self.topic["data"]["already-normalized-ø"] = node
        self.assertIn("/already-normalized-%C3%B8#kapittel-2", self.build()[self.protocols[0]]["current"]["url"])


if __name__ == "__main__":
    unittest.main()
