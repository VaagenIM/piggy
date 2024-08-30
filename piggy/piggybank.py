import json
import os
from pathlib import Path

from turtleconverter import mdfile_to_sections

from piggy import AssignmentTemplate, PIGGYBANK_FOLDER, ASSIGNMENT_FILENAME_REGEX, INCLUDED_FOLDERS


def load_meta_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    if "name" not in data:
        data["name"] = path.parent.name
    return data


def get_piggymap_segment_from_path(path: str, piggymap: dict) -> tuple[dict, dict]:
    """Get the metadata and segment from a path."""
    segment = dict(piggymap.copy())
    meta = segment.get("meta", {})
    for path in path.split("/"):
        if not path:
            continue
        if path not in segment:
            return {}, {}
        meta = segment.get(path, {}).get("meta", {})
        segment = segment.get(path, {}).get("data", {})

    return meta, segment


def get_all_meta_from_path(path: str, piggymap: dict) -> dict:
    """Get all metadata from a path."""
    metadata = dict()

    data = piggymap.get(path.split("/")[0], {})
    for i, p in enumerate(path.split("/")):
        meta = data.get("meta", {})
        key = [k for k, v in AssignmentTemplate.get_dictmap().items() if v == i]
        match i:
            case 0:
                continue
            case 1 | 2 | 3 | 4:
                metadata[key[0]] = meta
            case _:
                break
        data = data.get("data", {}).get(p, {})
    return metadata


def get_template_from_path(path: str) -> str:
    """Get the directory name from a path."""
    t = AssignmentTemplate.get_template_from_index(len([x for x in path.split("/") if x]))
    if not t:
        return AssignmentTemplate.ASSIGNMENT.template
    return t


def generate_piggymap(path: Path, max_levels: int = 5, _current_level: int = 0):
    """
    Generate a dictionary of the directory structure of the given path

    This function is a bit hard to read, but it essentially recursively goes through the directory structure of the
    given path and generates a dictionary representing the structure of the piggymap folder and the assignment files
    within. Also includes metadata from the 'meta.json' files in the directories in the meta key of the dictionary for
    each directory as long as they have one.

    :param path: The path to the directory to generate the piggymap for
    :param max_levels: The max number of levels to search
    :param _current_level: The current level of recursion (used internally)
    :return: A dictionary representing the directory structure of the piggymap folder and the assignment files within
    """
    piggymap = dict()

    # We only want to go 5 levels deep, and we only want to include directories (or the assignment files)
    if not os.path.isdir(path) or _current_level == max_levels:
        return None
    for item in os.listdir(path):
        # TODO: Decouple into separate functions
        # If the item is a directory, we want to go deeper
        if os.path.isdir(f"{path}/{item}"):
            new_item = generate_piggymap(Path(f"{path}/{item}"), _current_level=_current_level + 1)
            if new_item:
                piggymap[item] = {"data": new_item}
                # If the folder contains a 'meta.json' file, we should add that as metadata to the folder
                piggymap[item]["meta"] = load_meta_json(Path(f"{path}/{item}/meta.json"))
            continue

        # TODO: Clean up this mess
        folder = str(path).split("/")[-1].split("\\")[-1]
        if folder in INCLUDED_FOLDERS and item.endswith(".md"):
            sections = mdfile_to_sections(Path(f"{path}/{item}"))
            piggymap[item] = {
                "path": Path(f"{path}/{item}"),
                "heading": sections["heading"],
                "meta": sections["meta"],
                "type": folder,
            }
            continue

        # If the item is a file, we want to check if it's a valid assignment file
        match = ASSIGNMENT_FILENAME_REGEX.match(item)
        if not match:
            continue
        assignment_path = Path(f"{path}/{item}")
        sections = mdfile_to_sections(assignment_path)

        piggymap[item.replace(".md", "")] = {
            "path": assignment_path,
            "assignment_name": match.group(1).strip(),
            "level": match.group(2).strip(),
            "level_name": sections["heading"],  # match.group(3).strip(),
            "heading": sections["heading"],
            "meta": sections["meta"],
            "type": "assignment",
        }

    def recursive_sort(data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = recursive_sort(value)
        return dict(sorted(data.items()))

    return recursive_sort(piggymap)


PIGGYMAP = generate_piggymap(PIGGYBANK_FOLDER)


# DEVTOOL
def __update_piggymap():
    global PIGGYMAP
    print("Rebuilding piggymap")
    PIGGYMAP = generate_piggymap(PIGGYBANK_FOLDER)
    print("Piggymap rebuilt")
