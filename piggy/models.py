import json
from pathlib import Path


def get_languages():
    with open(Path("piggy/data/language-data.json"), "r", encoding="utf-8") as language_file:
        return json.load(language_file)


# Add key to all languages for ease of use
LANGUAGES = get_languages()
