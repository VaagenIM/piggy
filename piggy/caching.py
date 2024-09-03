from pathlib import Path
from typing import Callable

from flask import Response, render_template
from turtleconverter import mdfile_to_sections, ConversionError

from piggy import (
    ASSIGNMENT_ROUTE,
    MEDIA_ROUTE,
    PIGGYBANK_FOLDER,
    AssignmentTemplate,
)
from piggy.exceptions import PiggyHTTPException
from piggy.models import LANGUAGES
from piggy.piggybank import (
    get_all_meta_from_path,
    PIGGYMAP,
    get_template_from_path,
    get_piggymap_segment_from_path,
    get_assignment_data_from_path,
)
from piggy.utils import (
    get_supported_languages,
    normalize_path_to_str,
    generate_summary_from_mkdocs_html,
    lru_cache_wrapper,
)


def cache_directory(
    segment: dict, directory_fn: Callable[[str], Response], assignment_fn: Callable[[Path], Response], _path: str = ""
):
    for key, value in segment.items():
        print(f"Caching: {_path}/{key}")
        directory_fn(f"{_path}/{key}".strip("/"))
        # If we are just above the assignment level, its children will be the assignments
        if len(_path.split("/")) == AssignmentTemplate.ASSIGNMENT.index - 1:
            for assignment, assignment_data in value.get("data", {}).items():
                assignment_path = f"{_path}/{key}/{assignment}".strip("/")
                assignment_path = Path(f"{PIGGYBANK_FOLDER}/{assignment_path}.md")
                assignment_fn(assignment_path)
                [
                    assignment_fn(Path(f"{assignment_path.parent}/translations/{lang}/{assignment}.md"))
                    for lang in LANGUAGES.keys()
                    if Path(f"{assignment_path.parent}/translations/{lang}/{assignment}.md").exists()
                ]
        # If we are at the assignment level, we are done
        elif len(_path.split("/")) > AssignmentTemplate.ASSIGNMENT.index - 1:
            return
        else:
            cache_directory(
                value.get("data", {}), directory_fn=directory_fn, assignment_fn=assignment_fn, _path=f"{_path}/{key}"
            )


@lru_cache_wrapper
def _render_assignment(p: Path) -> Response:
    """Render an assignment from a Path object."""
    if not p.exists():
        raise PiggyHTTPException("Assignment not found", status_code=404)
    try:
        sections = mdfile_to_sections(p)
        print("Rendering:", p)
    except ConversionError:
        raise PiggyHTTPException("Error: Could not render assignment", status_code=500)

    lang = ""
    assignment_path = p
    if p.parents[1].name == "translations":
        lang = p.parent.name
        assignment_path = p.parents[2] / p.name

    current_language = LANGUAGES.get(lang, "")["name"]

    # Get the assignment data
    assignment_data = get_assignment_data_from_path(assignment_path, PIGGYMAP).copy()
    meta = assignment_data.get("meta", {}).copy()
    if "summary" not in meta:
        meta["summary"] = generate_summary_from_mkdocs_html(sections["body"])
    assignment_data.pop("meta")

    render = render_template(
        AssignmentTemplate.ASSIGNMENT.template,
        content=sections,
        meta={**meta, **get_all_meta_from_path(str(p.parent), PIGGYMAP)},
        current_language=current_language,
        supported_languages=get_supported_languages(assignment_path=assignment_path),
        media_abspath=f"/{MEDIA_ROUTE}/{p.parent}",
        abspath=f"/{ASSIGNMENT_ROUTE}/{p}",
        **assignment_data,  # Unpack the remainding assignment data from piggymap
    )
    return Response(render, mimetype="text/html", status=200)


@lru_cache_wrapper
def _render_assignment_wildcard(path="", lang="") -> Response:
    """
    Render the webpage for a given path.

    Keeps track of template_type (assignments_root, year_level, class_name, subject, topic) based on the path.
    Gets the relevant piggymap from the path. (key = child content, value = dict with relevant child data + meta)
    """
    template_type = get_template_from_path(path)
    metadata, segment = get_piggymap_segment_from_path(path, PIGGYMAP)
    metadata = {**metadata, **get_all_meta_from_path(path, PIGGYMAP)}

    media_abspath = f"/{MEDIA_ROUTE}/{path}" if path else f"/{MEDIA_ROUTE}"
    abspath = f"/{ASSIGNMENT_ROUTE}/{path}" if path else f"/{ASSIGNMENT_ROUTE}"

    # If we are at the final level (assignment), render the assignment
    if len(path.split("/")) == AssignmentTemplate.ASSIGNMENT.index:
        path_from_segment = normalize_path_to_str(segment.get("path", ""), replace_spaces=False)
        path, assignment = str(path_from_segment).rsplit("/", 1)
        if lang:
            assignment = f"translations/{lang}/{assignment}"
        return _render_assignment(Path(f"{path}/{assignment}"))

    # Render the appropriate template
    return Response(
        render_template(
            template_type, meta=metadata, segment=segment, path=path, media_abspath=media_abspath, abspath=abspath
        ),
        200,
    )
