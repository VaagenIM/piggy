import unittest
from pathlib import Path
from types import SimpleNamespace

from frozendict.cool import deepfreeze
from jinja2 import Environment, FileSystemLoader

from piggy.sitemap import get_legacy_sources
from piggy.glossary import (
    GlossaryValidationError,
    build_glossary_index,
    norwegian_sort_key,
)


def _page(title, page_type=None, **metadata):
    return {
        "path": Path(f"/tmp/{title}.md"),
        "level_name": title,
        "meta": {"title": title, "page_type": page_type, **metadata},
        "translation_meta": {},
    }


class GlossaryTest(unittest.TestCase):
    def setUp(self):
        self.pages = {
            "nettverksenhet": _page(
                "Nettverksenhet",
                "reference",
                reference_kind="glossary",
                glossary={"id": "nettverksenhet", "term": "Nettverksenhet"},
            ),
            "ruter": _page(
                "Ruter",
                "reference",
                reference_kind="glossary",
                glossary={
                    "id": "ruter",
                    "term": "Ruter",
                    "english": "router",
                    "is_a": ["nettverksenhet"],
                    "related": ["svitsj"],
                    "legacy_paths": ["Old/Level 1 - Router"],
                },
            ),
            "svitsj": _page(
                "Svitsj",
                "reference",
                reference_kind="glossary",
                glossary={
                    "id": "svitsj",
                    "term": "Svitsj",
                    "english": "switch",
                    "is_a": ["nettverksenhet"],
                },
            ),
            "oppgave": _page("Lokalnett", "assignment", concepts=["ruter"]),
            "forklaring": _page("Nettverk forklart", "explanation", concepts=["ruter"]),
        }
        self.pages["ruter"]["translation_meta"] = {
            "eng": {
                "title": "Router",
                "glossary": {"id": "ruter", "term": "Router", "english": "router"},
            }
        }
        self.piggymap = {"Topic": {"meta": {}, "data": self.pages}}

    def test_builds_reverse_relations_concept_links_and_localized_terms(self):
        index = build_glossary_index(self.piggymap)
        device = index["by_id"]["nettverksenhet"]
        router = index["by_id"]["ruter"]

        self.assertEqual(device["types"], ["ruter", "svitsj"])
        self.assertEqual(router["related"], ["svitsj"])
        self.assertEqual(index["by_id"]["svitsj"]["related"], ["ruter"])
        self.assertEqual(router["used_in"][0]["title"], "Lokalnett")
        self.assertEqual(router["explained_in"][0]["title"], "Nettverk forklart")
        self.assertEqual(router["localized_terms"]["eng"], "Router")
        self.assertEqual(router["language_urls"]["eng"], "/main/Topic/ruter/lang/eng")
        self.assertEqual(index["legacy_routes"]["Old/Level_1_-_Router"], "Topic/ruter")

    def test_builds_index_from_a_deep_frozen_piggymap(self):
        # The app freezes the piggymap before indexing it, so lists arrive as tuples
        index = build_glossary_index(deepfreeze(self.piggymap))

        self.assertEqual(index["by_id"]["nettverksenhet"]["types"], ["ruter", "svitsj"])
        self.assertEqual(index["by_id"]["ruter"]["used_in"][0]["title"], "Lokalnett")

    def test_legacy_paths_share_the_source_of_the_renamed_page(self):
        sources = [
            ("/main/Topic/ruter", Path("Topic/Ruter.md")),
            ("/main/Topic/ruter/lang/eng", Path("Topic/translations/eng/Ruter.md")),
            ("/main/Topic/svitsj", Path("Topic/Svitsj.md")),
        ]

        self.assertEqual(
            get_legacy_sources(sources, {"Old/Level_1_-_Router": "Topic/ruter"}),
            [
                ("/main/Old/Level_1_-_Router", Path("Topic/Ruter.md")),
                ("/main/Old/Level_1_-_Router/lang/eng", Path("Topic/translations/eng/Ruter.md")),
            ],
        )

    def test_rejects_missing_relationship_targets_and_cycles(self):
        self.pages["ruter"]["meta"]["glossary"]["is_a"] = ["missing"]
        with self.assertRaisesRegex(GlossaryValidationError, "references missing ID"):
            build_glossary_index(self.piggymap)

        self.pages["ruter"]["meta"]["glossary"]["is_a"] = ["nettverksenhet"]
        self.pages["nettverksenhet"]["meta"]["glossary"]["is_a"] = ["ruter"]
        with self.assertRaisesRegex(GlossaryValidationError, "contains a cycle"):
            build_glossary_index(self.piggymap)

    def test_rejects_ambiguous_duplicate_terms_without_distinguishing_notes(self):
        self.pages["svitsj"]["meta"]["glossary"]["term"] = "Ruter"
        with self.assertRaisesRegex(GlossaryValidationError, "distinct disambiguation"):
            build_glossary_index(self.piggymap)

    def test_norwegian_sort_order_places_special_letters_after_z(self):
        terms = ["Ål", "Zebra", "Øye", "Ære"]

        self.assertEqual(
            sorted(terms, key=norwegian_sort_key),
            ["Zebra", "Ære", "Øye", "Ål"],
        )

    def test_relation_partial_renders_glossary_and_concept_links(self):
        index = build_glossary_index(self.piggymap)
        templates = Path(__file__).resolve().parents[1] / "piggy" / "templates"
        environment = Environment(loader=FileSystemLoader(templates), autoescape=False)
        template = environment.get_template("partials/parts/glossary-relations.html")

        rendered = template.render(
            meta=self.pages["ruter"]["meta"],
            glossary_index=index,
            current_language=SimpleNamespace(key="eng"),
            github_pages=True,
        )

        self.assertIn("Er en type", rendered)
        self.assertIn("Nettverksenhet", rendered)
        self.assertIn("Beslektet med", rendered)
        self.assertIn("Svitsj", rendered)
        self.assertIn("Lokalnett", rendered)
        self.assertIn("Nettverk forklart", rendered)


if __name__ == "__main__":
    unittest.main()
