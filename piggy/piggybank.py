import json
import os
import timeit
from pathlib import Path

import markupsafe
import yaml
from frozendict.cool import deepfreeze

from piggy import AssignmentTemplate, PIGGYBANK_FOLDER, ASSIGNMENT_FILENAME_REGEX
from piggy.utils import normalize_path_to_str, lru_cache_wrapper


def load_meta_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    if "name" not in data:
        data["name"] = path.parent.name.replace("_", " ")
    return data


# TODO: these could probably be combined into one function
@lru_cache_wrapper
def get_piggymap_segment_from_path(path: str or Path, piggymap: dict) -> tuple[dict, dict]:
    """Get the metadata and segment from a path."""
    path = normalize_path_to_str(path, replace_spaces=True)
    segment = piggymap.copy()
    meta = segment.get("meta", {})
    for path in path.split("/"):
        if not path:
            continue
        if path not in segment:
            return {}, {}
        meta = segment.get(path, {}).get("meta", {})
        segment = segment.get(path, {})
        # Get the data if it exists, if not get segment minus the meta
        segment = segment.get("data", {k: v for k, v in segment.items() if k != "meta"})
    return meta, segment


# TODO: these could probably be combined into one function
def get_all_meta_from_path(path: str or Path, piggymap: dict) -> dict:
    """Get all metadata from a path."""
    metadata = dict()

    path = normalize_path_to_str(path, replace_spaces=True)

    data = piggymap.get(path.split("/")[0], {})
    for i, p in enumerate(path.split("/"), 1):
        meta = data.get("meta", {})
        key = [k for k, v in AssignmentTemplate.get_dictmap().items() if v == i - 1]
        match i:
            case 1:
                continue
            case 2 | 3 | 4:
                metadata[key[0]] = meta
            case 5:
                metadata[key[0]] = meta
                break
            case _:
                break
        data = data.get("data", {}).get(p, {})
    if len(path.split("/")) == AssignmentTemplate.ASSIGNMENT.index:
        metadata[AssignmentTemplate.LEVELS_DATA.name] = data
    return metadata


# TODO: these could probably be combined into one function
def get_assignment_data_from_path(path: str or Path, piggymap: dict) -> dict:
    """Get the assignment data from a path."""
    path = normalize_path_to_str(path, replace_spaces=True, normalize_url=True, remove_ext=True)
    segment = piggymap.copy()
    for i, p in enumerate(path.split("/")):
        if i == 0:
            continue
        if i == len(path.split("/")) - 1:
            segment = segment.get(p, {})
            break
        segment = segment.get(p, {}).get("data", {})
    return segment


@lru_cache_wrapper
def get_template_from_path(path: str) -> str:
    """Get the directory name from a path."""
    t = AssignmentTemplate.get_template_from_index(len([x for x in path.split("/") if x]))
    if not t:
        return AssignmentTemplate.ASSIGNMENT.template
    return t


def get_frontmatter_from_file(path: Path) -> dict:
    data = ""
    frontmatter = {}
    fallback_title = path.stem.replace("_", " ")
    with open(path, "r", encoding="utf-8") as f:
        if f.readline().strip() == "---":
            for line in f:
                if line.strip() == "---":
                    break
                data += line
        f.seek(0)
        for line in f:
            if line.strip().startswith("# "):
                fallback_title = line.lstrip("#").strip()
                break
    try:
        frontmatter = yaml.unsafe_load(data)
    except yaml.YAMLError:
        print(f"Error parsing frontmatter in {path}")

    if not frontmatter:
        frontmatter = {}

    frontmatter["title"] = frontmatter.get("title", fallback_title)
    return {k: str(markupsafe.escape(v)) for k, v in frontmatter.items()}


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
        i = item.replace(" ", "_")  # We don't want spaces in the keys for pretty URLs
        # If the item is a directory, we want to go deeper
        if os.path.isdir(f"{path}/{item}"):
            new_item = generate_piggymap(Path(f"{path}/{item}"), _current_level=_current_level + 1)
            if new_item:
                piggymap[i] = {"data": new_item}
                # If the folder contains a 'meta.json' file, we should add that as metadata to the folder
                piggymap[i]["meta"] = load_meta_json(Path(f"{path}/{item}/meta.json"))
                piggymap[i]["meta"]["system_path"] = Path(f"{path}/{item}")
            continue

        # If the item is a file, we want to check if it's a valid assignment file
        match = ASSIGNMENT_FILENAME_REGEX.match(i)
        if not match:
            continue
        assignment_path = Path(f"{path}/{item}")

        frontmatter = get_frontmatter_from_file(assignment_path)

        # Get translations metadata
        translation_meta = dict()
        for lang in os.listdir(f"{path}/translations") if os.path.isdir(f"{path}/translations") else []:
            if not os.path.exists(f"{path}/translations/{lang}/{item}"):
                continue
            translation_meta[lang] = get_frontmatter_from_file(Path(f"{path}/translations/{lang}/{item}"))

        assignment_key = normalize_path_to_str(i, replace_spaces=True, normalize_url=True, remove_ext=True)
        piggymap[assignment_key] = {
            "path": assignment_path,
            "level": match.group(1).strip(),
            "level_name": frontmatter["title"],
            "heading": frontmatter["title"],
            "meta": frontmatter,
            "translation_meta": translation_meta,
        }

    def recursive_sort(data):
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = recursive_sort(value)
        return dict(sorted(data.items()))

    return recursive_sort(piggymap)


def stringify_paths(d: dict) -> dict:
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = unfreeze(value)
        if isinstance(value, Path):
            d[key] = str(value.as_posix())
    return d


@lru_cache_wrapper
def unfreeze(d):
    """
    Unfreeze a frozendict and convert all Path objects to strings, or just convert all Path objects to strings.
    """
    if isinstance(d, dict):
        d = dict(d.copy())
        return stringify_paths(d)
    elif isinstance(d, Path):
        return str(d.as_posix())
    return d


start_time = timeit.default_timer()
print("Building piggymap")
PIGGYMAP = deepfreeze(generate_piggymap(PIGGYBANK_FOLDER))
print(f"Piggymap built in {timeit.default_timer() - start_time:.2f} seconds")
