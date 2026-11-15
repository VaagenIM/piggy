PAGE_TYPES = frozenset({"tutorial", "how-to", "explanation", "reference", "assignment"})
TOPIC_TYPES = frozenset({"assignment", "exercise", "information", "extra"})

_LABELS = {
    "": {
        "tutorial": "Opplæring",
        "how-to": "Framgangsmåte",
        "explanation": "Forklaring",
        "reference": "Oppslag",
        "assignment": "Oppdrag",
    },
    "eng": {
        "tutorial": "Tutorial",
        "how-to": "How-to",
        "explanation": "Explanation",
        "reference": "Reference",
        "assignment": "Assignment",
    },
    "ukr": {
        "tutorial": "Навчання",
        "how-to": "Інструкція",
        "explanation": "Пояснення",
        "reference": "Довідка",
        "assignment": "Завдання",
    },
}


def page_type_label(value: str | None, language: str = "") -> str:
    """Return a localized display label without changing unknown values."""
    if not value:
        return ""
    labels = _LABELS.get(language, _LABELS[""])
    return labels.get(value, value)
