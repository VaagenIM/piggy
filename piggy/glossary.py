from __future__ import annotations

import re
import unicodedata
from collections import defaultdict
from collections.abc import Mapping

from piggy.utils import normalize_path_to_str

GLOSSARY_RELATIONS = ("is_a", "part_of", "uses", "related")
_GLOSSARY_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NORWEGIAN_ORDER = str.maketrans({"æ": "{", "ø": "|", "å": "}"})


class GlossaryValidationError(ValueError):
    """Raised when glossary metadata cannot form a consistent index."""


def norwegian_sort_key(value: str) -> str:
    """Sort Norwegian letters in the order æ, ø, å after z."""
    normalized = unicodedata.normalize("NFKD", value.casefold().translate(_NORWEGIAN_ORDER))
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    return normalized.translate(_NORWEGIAN_ORDER)


def _iter_pages(node: Mapping, path_parts: tuple[str, ...] = ()):
    for key, value in node.items():
        if not isinstance(value, Mapping):
            continue
        if "path" in value:
            yield "/".join((*path_parts, str(key))), value
            continue
        data = value.get("data", {})
        if isinstance(data, Mapping):
            yield from _iter_pages(data, (*path_parts, str(key)))


def _string_list(value, field: str, owner: str, errors: list[str]) -> list[str]:
    if value is None:
        return []
    # The piggymap is deep-frozen before the index is built, which turns YAML lists into tuples
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{owner}: {field} must be a list of non-empty strings")
        return []
    if len(set(value)) != len(value):
        errors.append(f"{owner}: {field} contains duplicate values")
    return list(value)


def _page_link(route: str, title: str, page_type: str | None) -> dict:
    return {"url": f"/main/{route}", "title": title, "page_type": page_type or ""}


def _has_cycle(graph: dict[str, list[str]]) -> bool:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        if any(visit(target) for target in graph.get(node, [])):
            return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(visit(node) for node in graph)


def build_glossary_index(piggymap: Mapping) -> dict:
    """Validate glossary metadata and build forward and derived page relations."""
    entries: dict[str, dict] = {}
    pages: list[dict] = []
    legacy_routes: dict[str, str] = {}
    errors: list[str] = []
    term_owners: dict[str, list[tuple[str, str | None]]] = defaultdict(list)

    for route, page in _iter_pages(piggymap):
        meta = page.get("meta", {})
        if not isinstance(meta, Mapping):
            continue
        page_type = meta.get("page_type")
        title = str(meta.get("title") or page.get("level_name") or route.rsplit("/", 1)[-1])
        translations = page.get("translation_meta", {})
        localized_titles = {"": title}
        language_urls = {}
        if isinstance(translations, Mapping):
            for language, translation_meta in translations.items():
                if isinstance(translation_meta, Mapping):
                    localized_titles[language] = str(translation_meta.get("title") or title)
                    language_urls[language] = f"/main/{route}/lang/{language}"
        page_data = {
            "route": route,
            "url": f"/main/{route}",
            "title": title,
            "page_type": page_type,
            "localized_titles": localized_titles,
            "language_urls": language_urls,
            "concepts": _string_list(meta.get("concepts"), "concepts", route, errors),
        }
        pages.append(page_data)

        glossary = meta.get("glossary")
        if meta.get("reference_kind") != "glossary":
            if glossary is not None:
                errors.append(f"{route}: glossary data requires reference_kind: glossary")
            continue
        if page_type != "reference":
            errors.append(f"{route}: glossary entries must have page_type: reference")
        if not isinstance(glossary, Mapping):
            errors.append(f"{route}: reference_kind: glossary requires a glossary object")
            continue

        glossary_id = glossary.get("id")
        term = glossary.get("term")
        if not isinstance(glossary_id, str) or not _GLOSSARY_ID_RE.fullmatch(glossary_id):
            errors.append(f"{route}: glossary.id must be a stable lowercase kebab-case ID")
            continue
        if glossary_id in entries:
            errors.append(f"{route}: duplicate glossary.id {glossary_id}")
            continue
        if not isinstance(term, str) or not term.strip():
            errors.append(f"{route}: glossary.term must be a non-empty string")
            continue

        relations = {
            relation: _string_list(glossary.get(relation), f"glossary.{relation}", route, errors)
            for relation in GLOSSARY_RELATIONS
        }
        admitted = _string_list(glossary.get("admitted"), "glossary.admitted", route, errors)
        english = glossary.get("english", "")
        if not isinstance(english, str):
            errors.append(f"{route}: glossary.english must be a string")
            english = ""
        disambiguation = glossary.get("disambiguation")
        if disambiguation is not None and not isinstance(disambiguation, str):
            errors.append(f"{route}: glossary.disambiguation must be a string")
            disambiguation = None

        translation_terms = []
        search_terms = [term.strip(), english, *admitted]
        term_owners[term.strip().casefold()].append((glossary_id, disambiguation))
        for admitted_term in admitted:
            term_owners[admitted_term.strip().casefold()].append((glossary_id, disambiguation))
        if english:
            term_owners[f"eng:{english.casefold()}"].append((glossary_id, disambiguation))
        localized_terms = {"": term.strip()}
        if isinstance(translations, Mapping):
            for language, translation_meta in translations.items():
                if not isinstance(translation_meta, Mapping):
                    errors.append(f"{route}: translation {language} metadata must be an object")
                    continue
                translated_glossary = translation_meta.get("glossary")
                if translated_glossary is None:
                    continue
                if not isinstance(translated_glossary, Mapping):
                    errors.append(f"{route}: translation {language} glossary must be an object")
                    continue
                if translated_glossary.get("id") != glossary_id:
                    errors.append(f"{route}: translation {language} must keep glossary.id {glossary_id}")
                for relation in GLOSSARY_RELATIONS:
                    # A frozen piggymap stores lists as tuples; compare the values, not the container type
                    translated_relation = translated_glossary.get(relation)
                    if isinstance(translated_relation, (list, tuple)):
                        translated_relation = list(translated_relation)
                    if relation in translated_glossary and translated_relation != relations[relation]:
                        errors.append(f"{route}: translation {language} must keep glossary.{relation}")
                translated_term = translated_glossary.get("term")
                if translated_term is not None and (
                    not isinstance(translated_term, str) or not translated_term.strip()
                ):
                    errors.append(f"{route}: translation {language} glossary.term must be a non-empty string")
                if isinstance(translated_term, str) and translated_term.strip():
                    translation_terms.append((language, translated_term.strip()))
                    search_terms.append(translated_term.strip())
                    localized_terms[language] = translated_term.strip()
                    term_owners[f"{language}:{translated_term.strip().casefold()}"].append(
                        (glossary_id, disambiguation)
                    )
                translated_english = translated_glossary.get("english")
                if translated_english is not None and not isinstance(translated_english, str):
                    errors.append(f"{route}: translation {language} glossary.english must be a string")
                    translated_english = ""
                if isinstance(translated_english, str) and translated_english:
                    translation_terms.append((language, translated_english))
                    search_terms.append(translated_english)
                    term_owners[f"eng:{translated_english.casefold()}"].append((glossary_id, disambiguation))
                translated_admitted = _string_list(
                    translated_glossary.get("admitted"),
                    f"translation {language} glossary.admitted",
                    route,
                    errors,
                )
                translation_terms.extend((language, value) for value in translated_admitted)
                search_terms.extend(translated_admitted)
                for admitted_term in translated_admitted:
                    term_owners[f"{language}:{admitted_term.strip().casefold()}"].append(
                        (glossary_id, disambiguation)
                    )

        legacy_paths = _string_list(glossary.get("legacy_paths"), "glossary.legacy_paths", route, errors)
        for legacy_path in legacy_paths:
            normalized = normalize_path_to_str(
                legacy_path, normalize_page_path=True, normalize_url=True, remove_ext=True
            )
            if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
                errors.append(f"{route}: unsafe glossary.legacy_paths value {legacy_path!r}")
                continue
            if normalized in legacy_routes or normalized in {entry["route"] for entry in entries.values()}:
                errors.append(f"{route}: duplicate glossary legacy route {legacy_path!r}")
                continue
            legacy_routes[normalized] = route

        definition = meta.get("description", "")
        entries[glossary_id] = {
            "id": glossary_id,
            "term": term.strip(),
            "english": english,
            "admitted": admitted,
            "terms": list(dict.fromkeys(value for value in search_terms if value)),
            "translation_terms": translation_terms,
            "description": definition if isinstance(definition, str) else "",
            "disambiguation": disambiguation,
            "route": route,
            "url": page_data["url"],
            "language_urls": language_urls,
            "localized_terms": localized_terms,
            "title": title,
            "page_type": page_type,
            "relations": relations,
            "types": [],
            "parts": [],
            "used_by": [],
            "related": [],
            "explained_in": [],
            "used_in": [],
        }

    canonical_routes = {page["route"] for page in pages}
    for legacy_route in legacy_routes:
        if legacy_route in canonical_routes:
            errors.append(f"glossary legacy route {legacy_route!r} collides with a current page")

    for normalized_term, owners in term_owners.items():
        distinct_owners = {glossary_id: note for glossary_id, note in owners}
        if len(distinct_owners) < 2:
            continue
        disambiguations = list(distinct_owners.values())
        if any(not note for note in disambiguations) or len(set(disambiguations)) != len(disambiguations):
            errors.append(f"duplicate glossary term {normalized_term!r} requires distinct disambiguation notes")

    for glossary_id, entry in entries.items():
        for relation, targets in entry["relations"].items():
            for target in targets:
                if target not in entries:
                    errors.append(f"{glossary_id}: glossary.{relation} references missing ID {target}")
                elif target == glossary_id:
                    errors.append(f"{glossary_id}: glossary.{relation} cannot reference itself")
                elif relation == "is_a":
                    entries[target]["types"].append(glossary_id)
                elif relation == "part_of":
                    entries[target]["parts"].append(glossary_id)
                elif relation == "uses":
                    entries[target]["used_by"].append(glossary_id)
                elif relation == "related":
                    entry["related"].append(target)
                    entries[target]["related"].append(glossary_id)

    for relation in ("is_a", "part_of"):
        graph = {
            glossary_id: [target for target in entry["relations"][relation] if target in entries]
            for glossary_id, entry in entries.items()
        }
        if _has_cycle(graph):
            errors.append(f"glossary.{relation} contains a cycle")

    for page in pages:
        for glossary_id in page["concepts"]:
            if glossary_id not in entries:
                errors.append(f"{page['url']}: concepts references missing glossary ID {glossary_id}")
                continue
            target = entries[glossary_id]
            relation = "used_in" if page["page_type"] == "assignment" else "explained_in"
            target[relation].append(page)

    if errors:
        raise GlossaryValidationError("\n".join(errors))

    for entry in entries.values():
        for field in ("types", "parts", "used_by", "related"):
            entry[field] = sorted(
                set(entry[field]),
                key=lambda glossary_id: norwegian_sort_key(entries[glossary_id]["term"]),
            )
        for field in ("explained_in", "used_in"):
            entry[field].sort(key=lambda page: norwegian_sort_key(page["title"]))

    return {"by_id": entries, "legacy_routes": legacy_routes}
