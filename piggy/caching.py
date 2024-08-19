import os
from functools import lru_cache
from pathlib import Path
from typing import Callable

from flask import Response, render_template
from turtleconverter import mdfile_to_sections, ConversionError

from piggy import SUPPORTED_LANGUAGES, ASSIGNMENT_ROUTE, MEDIA_ROUTE, PIGGYBANK_FOLDER


def lru_cache_wrapper(func):
    if os.environ.get('USE_CACHE', '1') == '1':
        return lru_cache()(func)
    return func


def cache_directory(segment: dict,
                    directory_fn: Callable[[str], str],
                    assignment_fn: Callable[[Path], Response],
                    _path: str = ''):
    for key, value in segment.items():
        print(f'Caching: {_path}/{key}')
        directory_fn(f'{_path}/{key}'.strip('/'))
        if _path.count('/') == 3:
            for assignment, assignment_data in value.get('data', {}).items():
                assignment_path = f'{_path}/{key}/{assignment}'.strip('/')
                assignment_path = Path(f'{PIGGYBANK_FOLDER}/{assignment_path}.md')
                assignment_fn(assignment_path)
                [assignment_fn(Path(f'{assignment_path.parent}/translations/{lang}/{assignment}.md'))
                 for lang in SUPPORTED_LANGUAGES.keys()]
        elif _path.count('/') > 3:
            return
        else:
            cache_directory(value.get('data', {}), f'{_path}/{key}')


@lru_cache_wrapper
def _render_assignment(p: Path) -> Response:
    """Render an assignment from a Path object."""
    if not p.exists():
        # TODO: Raise a custom error
        return Response('Error: Assignment not found', status=404)
    try:
        sections = mdfile_to_sections(p)
        print('Rendering:', p)
    except ConversionError:
        # TODO: Raise a custom error
        return Response('Error: Could not render assignment', status=500)
    render = render_template('assignments/5-assignment.html',
                             content=sections,
                             current_language=SUPPORTED_LANGUAGES.get('name', 'Unknown'),
                             supported_languages=SUPPORTED_LANGUAGES,
                             path=p,
                             media_abspath=f'/{MEDIA_ROUTE}/{p.parent}/media',
                             abspath=f'/{ASSIGNMENT_ROUTE}/{p}')
    return Response(render, mimetype='text/html', status=200)
