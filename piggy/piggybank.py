import json
import os
import timeit
from pathlib import Path

import markupsafe
import yaml
from frozendict.cool import deepfreeze

from piggy import (
    IMG_FMT,
    ASSIGNMENT_FILENAME_REGEX,
    AssignmentTemplate,
    PIGGYBANK_FOLDER,
    generate_shortlink,
)
from piggy.utils import normalize_path_to_str, lru_cache_wrapper


def load_meta_json(path: Path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    data["oinkdata"] = load_oink_file(path)
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


def get_piggymap_page_from_path(path: str or Path, piggymap: dict) -> dict:
    """Get the page data stored at a path."""
    path = normalize_path_to_str(path, replace_spaces=True)
    segment = piggymap
    parts = [part for part in path.split("/") if part]
    for index, part in enumerate(parts):
        page = segment.get(part, {})
        if index == len(parts) - 1:
            return page
        segment = page.get("data", {})
    return {}


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
        if i <= PIGGYBANK_FOLDER.as_posix().count("/"):
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


def load_oink_file(path: Path) -> dict:
    """Load a JSON .oink file adjacent to a metadata or markdown file, if it exists."""
    oink_path = path.with_suffix(".oink")
    if not oink_path.exists():
        return {}
    try:
        with open(oink_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        print(f"Error parsing oink file {oink_path}")
    return {}


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


def _register_shortlink(shortlink_map: dict, meta: dict, fallback_identity: str, target: str, title: str):
    identity = meta.get("uuid") or meta.get("oinkdata", {}).get("uuid") or fallback_identity
    shortlink = generate_shortlink(identity)
    if shortlink in shortlink_map:
        raise ValueError(f"Duplicate page shortlink: {shortlink}")

    topic_path = target.removeprefix("/main/").rsplit("/", 1)[0]
    description = meta.get("description") or meta.get("oinkdata", {}).get("summary") or meta.get("summary", "")
    shortlink_map[shortlink] = {
        "target": target,
        "title": title,
        "description": description,
        "image": f"/img/{topic_path}/{meta.get('thumbnail', 'media/header')}.{IMG_FMT}?title={title}",
    }
    return shortlink


def generate_piggymap(
    path: Path,
    max_levels: int = 5,
    _current_level: int = 0,
    _url_path: str = "",
    _shortlink_map: dict | None = None,
):
    """
    Generate a dictionary of the directory structure of the given path

    This function is a bit hard to read, but it essentially recursively goes through the directory structure of the
    given path and generates a dictionary representing the structure of the piggymap folder and the assignment files
    within. Also includes metadata from the 'meta.json' files in the directories in the meta key of the dictionary for
    each directory as long as they have one.

    :param path: The path to the directory to generate the piggymap for
    :param max_levels: The max number of levels to search
    :param _current_level: The current level of recursion (used internally)
    :param _url_path: The url path of the piggymap folder
    :return: A dictionary representing the directory structure of the piggymap folder and the assignment files within
    """
    piggymap = dict()
    shortlink_map = _shortlink_map if _shortlink_map is not None else {}

    # We only want to go 5 levels deep, and we only want to include directories (or the assignment files)
    if not os.path.isdir(path) or _current_level == max_levels:
        return None
    for item in os.listdir(path):
        # TODO: Decouple into separate functions
        i = item.replace(" ", "_")  # We don't want spaces in the keys for pretty URLs
        # If the item is a directory, we want to go deeper
        if os.path.isdir(f"{path}/{item}"):
            new_item = generate_piggymap(
                Path(f"{path}/{item}"),
                _current_level=_current_level + 1,
                _url_path=f"{_url_path}/{i}",
                _shortlink_map=shortlink_map,
            )
            if new_item:
                piggymap[i] = {"data": new_item}
                # If the folder contains a 'meta.json' file, we should add that as metadata to the folder
                piggymap[i]["meta"] = load_meta_json(Path(f"{path}/{item}/meta.json"))
                piggymap[i]["meta"]["system_path"] = Path(f"{path}/{item}")
                page_url = f"{_url_path}/{i}".strip("/")
                piggymap[i]["shortlink"] = _register_shortlink(
                    shortlink_map,
                    piggymap[i]["meta"],
                    page_url,
                    f"/main/{page_url}",
                    piggymap[i]["meta"]["name"],
                )
            # Subjects should have their type set to exercise by default
            if _current_level == AssignmentTemplate.TOPIC.index - 1 and i in piggymap:
                piggymap[i]["meta"]["type"] = piggymap[i]["meta"].get("type", "exercise")
            continue

        # If the item is a file, we want to check if it's a valid assignment file
        match = ASSIGNMENT_FILENAME_REGEX.match(i)
        if not match:
            continue
        assignment_path = Path(f"{path}/{item}")

        frontmatter = get_frontmatter_from_file(assignment_path)
        assignment_oink = load_oink_file(assignment_path)
        frontmatter.update(assignment_oink)

        # Default thumbnail to the assignment group's header image if not specified
        if "thumbnail" not in frontmatter:
            frontmatter["thumbnail"] = "media/header"

        # Get translations metadata
        translation_meta = dict()
        for lang in os.listdir(f"{path}/translations") if os.path.isdir(f"{path}/translations") else []:
            if not os.path.exists(f"{path}/translations/{lang}/{item}"):
                continue
            translation_path = Path(f"{path}/translations/{lang}/{item}")
            trans_frontmatter = get_frontmatter_from_file(translation_path)
            trans_oink = load_oink_file(translation_path)
            if not trans_oink and assignment_oink:
                trans_oink = {**assignment_oink, "oinkdata": {}}
            trans_frontmatter.update(trans_oink)
            translation_meta[lang] = trans_frontmatter

        assignment_key = normalize_path_to_str(i, replace_spaces=True, normalize_url=True, remove_ext=True)
        assignment_url = f"{_url_path}/{assignment_key}".strip("/")
        shortlink_target = f"/main/{assignment_url}"
        piggymap[assignment_key] = {
            "path": assignment_path,
            "level": match.group(1).strip(),
            "level_name": frontmatter["title"],
            "heading": frontmatter["title"],
            "shortlink": _register_shortlink(
                shortlink_map,
                frontmatter,
                assignment_key,
                shortlink_target,
                frontmatter["title"],
            ),
            "shortlink_target": shortlink_target,
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
SHORTLINK_MAP = {}
PIGGYMAP = deepfreeze(generate_piggymap(PIGGYBANK_FOLDER, _shortlink_map=SHORTLINK_MAP))
SHORTLINK_MAP = deepfreeze(SHORTLINK_MAP)
print(f"Piggymap built in {timeit.default_timer() - start_time:.2f} seconds")
