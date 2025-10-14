import pytest

import sys
import os
import inspect

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)

sys.path.insert(0, parentdir)

from piggy import utils

def test_css_metadata_basic():
    dummy_path = "tests/test_data/test_css.css"

    result = utils.get_css_metadata(dummy_path)

    assert result['path'] == 'test_css'
    assert result["id"] == "0"
    assert result["name"] == "Test"
    assert result["description"] == "A testing theme"
    assert result["type"] == "dark"
    assert result["preview_style"] == "color: #ffffff;"


def test_css_metadata_no_metadata():
    dummy_path = "tests/test_data/test_empty_css.css"

    result = utils.get_css_metadata(dummy_path)

    assert result['path'] == 'test_empty_css'

# if there is some metadata in the CSS which has a wrong name, it should raise a ValueError (?), as it is invalid metadata
def test_css_metadata_wrong():
    dummy_path = "tests/test_data/test_wrong_css.css"

    with pytest.raises(ValueError):
        utils.get_css_metadata(dummy_path)
