import json
import tempfile
import unittest
import uuid
import warnings
from pathlib import Path

from piggy.page_types import PAGE_TYPES, TOPIC_TYPES, page_type_label
from piggy.piggybank import generate_piggymap, get_frontmatter_from_file, load_meta_json


class PageTypesTest(unittest.TestCase):
    def test_page_type_values_and_labels(self):
        self.assertEqual(
            PAGE_TYPES,
            {"tutorial", "how-to", "explanation", "reference", "assignment"},
        )
        self.assertTrue({"assignment", "exercise", "information", "extra"} <= TOPIC_TYPES)
        self.assertEqual(page_type_label("tutorial"), "Opplæring")
        self.assertEqual(page_type_label("tutorial", "eng"), "Tutorial")
        self.assertEqual(page_type_label("reference", "ukr"), "Довідка")
        self.assertEqual(page_type_label("assignment"), "Oppdrag")
        self.assertEqual(page_type_label("unrecognized"), "unrecognized")

    def test_frontmatter_keeps_structured_yaml_values_and_warns_on_unknown_type(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "term.md"
            path.write_text(
                "---\n"
                "page_type: reference\n"
                "reference_kind: glossary\n"
                "glossary:\n"
                "  id: example\n"
                "  term: '<Term & example>'\n"
                "  admitted: [router]\n"
                "  rank: 2\n"
                "  enabled: true\n"
                "---\n",
                encoding="utf-8",
            )
            metadata = get_frontmatter_from_file(path)
            self.assertEqual(metadata["glossary"]["admitted"], ["router"])
            self.assertEqual(metadata["glossary"]["rank"], 2)
            self.assertIs(metadata["glossary"]["enabled"], True)
            self.assertEqual(metadata["glossary"]["term"], "&lt;Term &amp; example&gt;")

            path.write_text("---\ndifficulty: 3\ntags: [a, b]\n---\n", encoding="utf-8")
            legacy = get_frontmatter_from_file(path)
            self.assertEqual(legacy["difficulty"], "3")
            self.assertIsInstance(legacy["tags"], str)

            for page_type in PAGE_TYPES:
                path.write_text(f"---\npage_type: {page_type}\n---\n", encoding="utf-8")
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    get_frontmatter_from_file(path)
                self.assertFalse(any("Unknown page_type" in str(item.message) for item in caught))

            path.write_text("---\npage_type: unknown\n---\n", encoding="utf-8")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                get_frontmatter_from_file(path)
            self.assertTrue(any("Unknown page_type" in str(item.message) for item in caught))

    def test_legacy_topic_types_default_and_level_free_glossary_pages(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directories = [
                root / "VG1",
                root / "VG1" / "IM",
                root / "VG1" / "IM" / "Subject",
            ]
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                (directory / "meta.json").write_text(
                    json.dumps({"uuid": str(uuid.uuid4())}),
                    encoding="utf-8",
                )

            for index, topic_type in enumerate(("assignment", "exercise", "information", "extra")):
                topic = directories[-1] / f"Topic {index}"
                topic.mkdir()
                (topic / "meta.json").write_text(
                    json.dumps({"type": topic_type, "uuid": str(uuid.uuid4())}),
                    encoding="utf-8",
                )
                (topic / "Level 1 - Example.md").write_text(
                    "---\nuuid: " + str(uuid.uuid4()) + "\n---\n# Example\n",
                    encoding="utf-8",
                )

            default_topic = directories[-1] / "Default"
            default_topic.mkdir()
            (default_topic / "meta.json").write_text(
                json.dumps({"uuid": str(uuid.uuid4())}),
                encoding="utf-8",
            )
            (default_topic / "Level 1 - Example.md").write_text(
                "---\nuuid: " + str(uuid.uuid4()) + "\n---\n# Example\n",
                encoding="utf-8",
            )

            glossary_topic = directories[-1] / "Glossary"
            glossary_topic.mkdir()
            (glossary_topic / "meta.json").write_text(
                json.dumps(
                    {
                        "type": "information",
                        "sibling_links": False,
                        "uuid": str(uuid.uuid4()),
                    }
                ),
                encoding="utf-8",
            )
            (glossary_topic / "Network device.md").write_text(
                "---\n"
                "page_type: reference\n"
                "reference_kind: glossary\n"
                "glossary:\n"
                "  id: network-device\n"
                "  term: Nettverksenhet\n"
                "uuid: " + str(uuid.uuid4()) + "\n"
                "---\n",
                encoding="utf-8",
            )

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                piggymap = generate_piggymap(root, _shortlink_map={})
            subject = piggymap["VG1"]["data"]["IM"]["data"]["Subject"]
            self.assertFalse(any("Unknown topic type" in str(item.message) for item in caught))
            for index, topic_type in enumerate(("assignment", "exercise", "information", "extra")):
                self.assertEqual(subject["data"][f"Topic_{index}"]["meta"]["type"], topic_type)
            self.assertEqual(subject["data"]["Default"]["meta"]["type"], "exercise")
            glossary_pages = subject["data"]["Glossary"]["data"]
            self.assertIn("Network_device", glossary_pages)
            self.assertIsNone(glossary_pages["Network_device"]["level"])

    def test_unknown_topic_type_warns(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "topic" / "meta.json"
            path.parent.mkdir()
            path.write_text(json.dumps({"type": "unknown"}), encoding="utf-8")

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                load_meta_json(path)
            self.assertTrue(any("Unknown topic type" in str(item.message) for item in caught))


if __name__ == "__main__":
    unittest.main()
