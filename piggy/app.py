import os
from functools import lru_cache
from pathlib import Path

from flask import Flask, send_file, request, render_template, Response, Blueprint
from turtleconverter import generate_static_files, mdfile_to_sections, ConversionError

from piggy.piggybank import generate_piggymap

# Ensure the working directory is the root of the project
os.chdir(os.path.dirname(Path(__file__).parent.absolute()))

PIGGYBANK_FOLDER = Path('piggybank')
PIGGYMAP = generate_piggymap(PIGGYBANK_FOLDER)

SUPPORTED_LANGUAGES = {
    '': {'name': 'Norsk'},
    'eng': {'name': 'English'},
    'ukr': {'name': 'Українська'},
}

# A prefix for the assignment URLs, to avoid conflicts with other routes
ASSIGNMENT_ROUTE = 'main'
# We can't have the media files have the same URL prefix as the assignments, as it would conflict
# with the wildcard route for the media files.
MEDIA_ROUTE = 'img'


# TODO: Logging
# TODO: Split up certain functions in this file into separate files

def get_piggymap_segment_from_path(path: str) -> tuple[dict, dict]:
    """Get the metadata and segment from a path."""
    segment = dict(PIGGYMAP.copy())
    meta = segment.get('meta', {})
    for path in path.split('/'):
        if not path:
            continue
        if path not in segment:
            return {}, {}
        meta = segment.get(path, {}).get('meta', {})
        segment = segment.get(path, {}).get('data', {})

    return meta, segment


def get_directory_name_from_path(path: str) -> str:
    """Get the directory name from a path."""
    # TODO: Use an enum?
    nest_level_dirname = {
        0: 'assignments_root',
        1: 'year_level',
        2: 'class_name',
        3: 'subject',
        4: 'topic',
    }
    path = path.split('/')
    return nest_level_dirname.get(len([x for x in path if x]), 'unknown')


@lru_cache
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
    render = render_template('assignment.html',
                             content=sections,
                             current_language=SUPPORTED_LANGUAGES.get('name', 'Unknown'),
                             supported_languages=SUPPORTED_LANGUAGES,
                             path=p,
                             media_abspath=f'/{MEDIA_ROUTE}/{p.parent}/media',
                             abspath=f'/{ASSIGNMENT_ROUTE}/{p}')
    return Response(render, mimetype='text/html', status=200)


def generate_static_files_wrapper():
    cwd = os.getcwd()
    os.chdir(os.path.dirname(Path(__file__).absolute()))
    generate_static_files()
    os.chdir(cwd)


def create_app():
    app = Flask(__name__, static_folder='static')

    assignment_route = Blueprint(ASSIGNMENT_ROUTE, __name__, url_prefix=f'/{ASSIGNMENT_ROUTE}')
    media_route = Blueprint(MEDIA_ROUTE, __name__, url_prefix=f'/{MEDIA_ROUTE}')

    generate_static_files_wrapper()

    @app.context_processor
    def context_processor():
        return {'ASSIGNMENT_URL_PREFIX': ASSIGNMENT_ROUTE,
                'MEDIA_URL_PREFIX': MEDIA_ROUTE,
                'piggymap': PIGGYMAP, }

    @app.route('/')
    @lru_cache
    def index():
        html = '<h1>Velkommen til Piggy!</h1>'
        html += f'\n<a href="/{ASSIGNMENT_ROUTE}"><button>Oppgaver</button></a>'
        return html

    @assignment_route.route(f'/<path:path>')
    @assignment_route.route(f'/')
    @lru_cache
    def render_assignment_directories(path=''):
        """
        Render the webpage for a given path.

        Keeps track of template_type (assignments_root, year_level, class_name, subject, topic) based on the path.
        Gets the relevant piggymap from the path. (key = child content, value = dict with relevant child data + meta)
        """
        path = path.strip('/')

        template_type = get_directory_name_from_path(path)
        metadata, segment = get_piggymap_segment_from_path(path)

        return render_template(f'{template_type}.html',
                               meta=metadata,
                               segment=segment,
                               path=path,
                               media_abspath=f'/{MEDIA_ROUTE}/{path}/media',
                               abspath=f'/{ASSIGNMENT_ROUTE}/{path}')

    @assignment_route.route(f'/<year_level>/<class_name>/<subject>/<topic>/<assignment>')
    def render_assignment(year_level, class_name, subject, topic, assignment, lang=''):
        """
        Render an assignment from the piggymap. Takes precedence over the wildcard route due to specificity.
        """
        # TODO: Simplify path handling (less parameters)?
        if request:  # Caching doesn't work with request context
            lang = request.cookies.get('lang', lang)
        if lang:
            assignment = f'translations/{lang}/{assignment}'
        path = f'{PIGGYBANK_FOLDER}/{year_level}/{class_name}/{subject}/{topic}'

        return _render_assignment(Path(f'{path}/{assignment}.md'))

    def cache_all_assignment_directories():
        def cache_directory(segment: dict, path: str = ''):
            for key, value in segment.items():
                print(f'Caching: {path}/{key}')
                render_assignment_directories(f'{path}/{key}'.strip('/'))
                if path.count('/') == 3:
                    for assignment, assignment_data in value.get('data', {}).items():
                        assignment_path = f'{path}/{key}/{assignment}'.strip('/')
                        assignment_path = Path(f'{PIGGYBANK_FOLDER}/{assignment_path}.md')
                        _render_assignment(assignment_path)
                        [_render_assignment(Path(f'{assignment_path.parent}/translations/{lang}/{assignment}.md'))
                         for lang in SUPPORTED_LANGUAGES.keys()]
                elif path.count('/') > 3:
                    return
                else:
                    cache_directory(value.get('data', {}), f'{path}/{key}')

        with app.app_context():
            cache_directory(PIGGYMAP)

    @media_route.route(f'/<path:wildcard>/media/<filename>')
    @assignment_route.route(f'<path:wildcard>/attachments/<filename>')
    def get_media_wildcard(wildcard, filename):
        """
        Get a media file from either the media or attachments folder.
        (only in MEDIA_URL_PREFIX or ASSIGNMENT_URL_PREFIX)
        """
        if request.path.split('/')[1] == MEDIA_ROUTE:
            wildcard = wildcard.replace(MEDIA_ROUTE, '', 1).strip('/')
            folder = 'media'
        else:
            folder = 'attachments'
        try:
            return send_file(Path(f'{PIGGYBANK_FOLDER}/{wildcard}/{folder}/{filename}').absolute())
        except FileNotFoundError:
            return send_file('static/img/placeholders/100x100.png')

    if not app.debug:
        cache_all_assignment_directories()

    app.register_blueprint(assignment_route)
    app.register_blueprint(media_route)

    return app
