import pytest

from pathlib import Path
from piggy.utils import get_css_metadata, get_themes
from unittest.mock import patch

# clear cache
def teardown_function(function):
    get_css_metadata.cache_clear()
    get_themes.cache_clear()


def test_get_css_metadata_valid(tmp_path):
    css_file = tmp_path / "test_theme.css"
    css_content = """/* METADATA
        id: 13
        name: Test Theme
        description: A testy test theme
        /*
        body {
            background-color: #ffffff;
        }
    """

    css_file.write_text(css_content)

    metadata = get_css_metadata(str(css_file))

    assert metadata is not None
    assert metadata["id"] == "13"
    assert metadata["name"] == "Test Theme"
    assert metadata["description"] == "A testy test theme"
    assert metadata["path"] == css_file.stem


def test_get_css_metadata_no_metadata(tmp_path):
    css_file = tmp_path / "no_metadata.css"
    css_content = """
        body {
            background-color: #ffffff;
        }
    """

    css_file.write_text(css_content)

    metadata = get_css_metadata(str(css_file))

    assert metadata is None


def test_get_css_metadata_invalid_extension(tmp_path):
    invalid_file = tmp_path / "invalid.txt"
    invalid_file.write_text("Some content yo")

    metadata = get_css_metadata(str(invalid_file))

    assert metadata is None


def test_get_css_metadata_invalid_metadata(tmp_path):
    css_file = tmp_path / "invalid_metadata.css"
    css_content = """/* METADATA
        id
        name: Invalid Theme test
        */
    """

    css_file.write_text(css_content)

    metadata = get_css_metadata(str(css_file))

    assert metadata == {'path': css_file.stem}


# test an entire themes folder

def test_get_themes(tmp_path, monkeypatch):
    first_css = tmp_path / "theme1.css"
    # ID 2 to test ordering
    first_css.write_text("""/* METADATA
        id: 2
        name: Theme number 1
        description: Testing the first theme
        /*
        """
    )

    second_css = tmp_path / "theme2.css"
    # ID 1 to test ordering (this should be first)
    second_css.write_text("""/* METADATA
        id: 1
        name: Theme number 2
        description: Testing the second theme
        /*
        """
    )

    monkeypatch.setattr("piggy.utils.THEME_PATH", str(tmp_path))

    themes = get_themes()

    assert len(themes) == 2
    assert themes[0]["id"] == "1"
    assert themes[0]["name"] == "Theme number 2"
    assert themes[1]["id"] == "2"
    assert themes[1]["name"] == "Theme number 1"


def test_get_themes_no_css_files(tmp_path, monkeypatch):
    monkeypatch.setattr("piggy.utils.THEME_PATH", str(tmp_path))

    themes = get_themes()

    assert themes == []


def test_get_themes_non_css_files(tmp_path, monkeypatch):
    (tmp_path / "file.txt").write_text("Very random randomness")
    monkeypatch.setattr("piggy.utils.THEME_PATH", str(tmp_path))

    themes = get_themes()

    assert themes == []