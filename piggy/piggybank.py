import json
import os
import re
from pathlib import Path

from turtleconverter import mdfile_to_sections

ASSIGNMENT_FILENAME_REGEX = re.compile(r"^.+ Level \d+ \- .+")


def load_meta_json(path: Path):
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def generate_piggymap(path: Path, max_levels: int = 5, _current_level: int = 0):
    """
    Generate a dictionary of the directory structure of the given path

    :param path: The path to the directory to generate the piggymap for
    :param max_levels: The max number of levels to search
    :param _current_level: The current level of recursion (used internally)
    :return: A dictionary representing the directory structure of the piggymap folder and the assignment files within
    """
    piggymap = dict()

    # TODO: If a folder contains a 'meta.json' file, we should add that as metadata to the folder

    # We only want to go 5 levels deep, and we only want to include directories (or the assignment files)
    if not os.path.isdir(path) or _current_level == max_levels:
        return None
    for item in os.listdir(path):
        # If the item is a directory, we want to go deeper
        if os.path.isdir(f'{path}/{item}'):
            new_item = generate_piggymap(Path(f'{path}/{item}'), _current_level=_current_level + 1)
            if new_item:
                piggymap[item] = {'item': new_item}
                # If the folder contains a 'meta.json' file, we should add that as metadata to the folder
                piggymap[item]['meta'] = load_meta_json(Path(f'{path}/{item}/meta.json'))
            continue
        # If the item is a file, we want to check if it's a valid assignment file

        if not ASSIGNMENT_FILENAME_REGEX.match(item):
            continue
        assignment_path = Path(f'{path}/{item}')
        sections = mdfile_to_sections(assignment_path)
        piggymap[item.replace('.md', '')] = {
            'path': assignment_path,
            'slug': item.replace('.md', ''),
            'heading': sections['heading'],
            'meta': sections['meta'],
        }
    return piggymap
