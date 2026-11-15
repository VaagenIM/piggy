import tempfile
import unittest
from pathlib import Path

from frozendict.cool import deepfreeze

from piggy.search import build_search_index


class GlossarySearchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        page = Path(self.tmp.name) / "Lokalnettverk.md"
        page.write_text("---\ntitle: Lokalnettverk\n---\n\n# Lokalnettverk\n\nNettverk i et avgrenset område.\n")
        glossary = {
            "id": "lokalnettverk",
            "term": "Lokalnettverk",
            "english": "local area network",
            "admitted": ["LAN", "lokalnett"],
        }
        self.piggymap = {
            "VG1": {
                "meta": {"name": "VG1"},
                "data": {
                    "Begreper": {
                        "meta": {"name": "Begreper"},
                        "data": {
                            "Lokalnettverk": {
                                "path": page,
                                "level_name": "Lokalnettverk",
                                "meta": {
                                    "title": "Lokalnettverk",
                                    "page_type": "reference",
                                    "reference_kind": "glossary",
                                    "glossary": glossary,
                                },
                                "translation_meta": {
                                    "eng": {
                                        "title": "Local area network",
                                        "glossary": {**glossary, "term": "Local area network"},
                                    }
                                },
                            },
                        },
                    },
                },
            },
        }

    def _terms(self, piggymap):
        [document] = [d for d in build_search_index(piggymap) if d["id"].endswith("Lokalnettverk")]
        return document["glossary_terms"]

    def test_glossary_terms_include_term_english_admitted_and_translations(self):
        terms = self._terms(self.piggymap)

        for expected in ("Lokalnettverk", "local area network", "LAN", "lokalnett", "Local area network"):
            self.assertIn(expected, terms)

    def test_glossary_terms_are_built_from_a_deep_frozen_piggymap(self):
        self.assertIn("LAN", self._terms(deepfreeze(self.piggymap)))


if __name__ == "__main__":
    unittest.main()
