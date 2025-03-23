from pathlib import Path
from typing import Callable, Optional

from flask import Response, render_template
from frozendict import deepfreeze
from turtleconverter import mdfile_to_sections, ConversionError

from piggy import (
    ASSIGNMENT_ROUTE,
    MEDIA_ROUTE,
    AssignmentTemplate,
)
from piggy.exceptions import PiggyHTTPException, PiggyErrorException
from piggy.models import LANGUAGES
from piggy.piggybank import (
    get_all_meta_from_path,
    generate_piggymap,
    get_template_from_path,
    get_piggymap_segment_from_path,
    get_assignment_data_from_path,
)
from piggy.utils import (
    get_supported_languages,
    generate_summary_from_mkdocs_html,
    normalize_path_to_str,
    lru_cache_wrapper,
)


def cache_directory(
    segment: dict,
    fn: Callable[[str, Optional[str]], Response],
    _path: str = "",
):
    """Cache the directory of assignments."""
    for key, value in segment.items():
        print(f"Caching: {_path}/{key}")
        fn(f"{_path}/{key}".strip("/"))

        # If we are just above the assignment level, its children will be the assignments
        if len(_path.split("/")) == AssignmentTemplate.ASSIGNMENT.index - 1:
            for assignment, assignment_data in value.get("data", {}).items():
                # Get the path of the assignment (Path object
                assignment_path_obj = segment.get(key, {}).get("data", {}).get(assignment, {}).get("path", Path(""))

                # Set the assignment path to a string with the right url format
                assignment_path = str(f"{_path}/{key}/{assignment}")

                if not assignment_path_obj.exists():
                    raise PiggyErrorException(f"Assignment not found: {assignment_path}")

                fn(assignment_path, "")
                [
                    fn(f"{assignment_path}", lang)
                    for lang in LANGUAGES.keys()
                    if Path(f"{assignment_path_obj.parent}/translations/{lang}/{assignment}.md").exists()
                ]
        # If we are at the assignment level, we are done
        elif len(_path.split("/")) > AssignmentTemplate.ASSIGNMENT.index - 1:
            return
        else:
            cache_directory(value.get("data", {}), fn=fn, _path=f"{_path}/{key}")


@lru_cache_wrapper
def _render_assignment(p: Path, extra_metadata=None) -> Response:
    """Render an assignment from a Path object."""

    extra_metadata = dict(extra_metadata)

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

    current_language = LANGUAGES.get(lang, "")

    # Get the assignment data
    assignment_data = dict(get_assignment_data_from_path(assignment_path, generate_piggymap()).copy())
    meta = dict(assignment_data.get("meta", {}).copy())
    if "summary" not in meta:
        meta["summary"] = generate_summary_from_mkdocs_html(sections["body"])
    assignment_data.pop("meta")

    all_metadata = dict({**meta, **get_all_meta_from_path(str(p.parent), generate_piggymap()), **extra_metadata})
    # Set the title to the assignment's title
    all_metadata["title"] = sections["meta"]["title"]

    render = render_template(
        AssignmentTemplate.ASSIGNMENT.template,
        content=sections,
        meta=all_metadata,
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
    metadata, segment = get_piggymap_segment_from_path(path, generate_piggymap())

    # If a piggymap segment is not found, raise a 404
    if not segment:
        raise PiggyHTTPException("Page not found", status_code=404)

    metadata = {**metadata, **get_all_meta_from_path(path, generate_piggymap())}

    media_abspath = f"/{MEDIA_ROUTE}/{path}" if path else f"/{MEDIA_ROUTE}"
    abspath = f"/{ASSIGNMENT_ROUTE}/{path}" if path else f"/{ASSIGNMENT_ROUTE}"

    # If we are at the final level (assignment), render the assignment
    if len(path.split("/")) == AssignmentTemplate.ASSIGNMENT.index:
        # Get the path name with forward slashes
        path_from_segment = normalize_path_to_str(segment.get("path", ""))

        # If the assignment is not found, raise a 404
        if not path_from_segment:
            raise PiggyHTTPException("Assignment not found", status_code=404)
        path, assignment = str(path_from_segment).rsplit("/", 1)

        # If a language is specified, set the assignment path to the translation
        if lang:
            assignment = f"translations/{lang}/{assignment}"

        # Render the assignment with the metadata (must be deepfrozen to be hashable)
        return _render_assignment(Path(f"{path}/{assignment}"), extra_metadata=deepfreeze(metadata))

    # Render the appropriate template (if it is not the final level)
    return Response(
        render_template(
            template_type, meta=metadata, segment=segment, path=path, media_abspath=media_abspath, abspath=abspath
        ),
        200,
    )
