import os
from pathlib import Path

from flask import Flask, send_file, request, render_template, Blueprint

from piggy import PIGGYMAP, PIGGYBANK_FOLDER, ASSIGNMENT_ROUTE, MEDIA_ROUTE
from piggy.caching import lru_cache_wrapper, _render_assignment, cache_directory
from piggy.piggybank import get_piggymap_segment_from_path, get_template_from_path
from piggy.util import generate_static_files_wrapper

# Ensure the working directory is the root of the project
os.chdir(os.path.dirname(Path(__file__).parent.absolute()))


# TODO: Logging


def create_app():
    app = Flask(__name__, static_folder='static')

    assignment_routes = Blueprint(ASSIGNMENT_ROUTE, __name__, url_prefix=f'/{ASSIGNMENT_ROUTE}')
    media_routes = Blueprint(MEDIA_ROUTE, __name__, url_prefix=f'/{MEDIA_ROUTE}')

    generate_static_files_wrapper()

    @app.context_processor
    def context_processor():
        """Context variables for all templates in the app."""
        return {'ASSIGNMENT_URL_PREFIX': ASSIGNMENT_ROUTE,
                'MEDIA_URL_PREFIX': MEDIA_ROUTE,
                'piggymap': PIGGYMAP, }

    @app.route('/')
    @lru_cache_wrapper
    def index():
        html = '<h1>Velkommen til Piggy!</h1>'
        html += f'\n<a href="/{ASSIGNMENT_ROUTE}"><button>Oppgaver</button></a>'
        return html

    @assignment_routes.route(f'/<path:path>')
    @assignment_routes.route(f'/')
    @lru_cache_wrapper
    def get_assignment_directory(path=''):
        """
        Render the webpage for a given path.

        Keeps track of template_type (assignments_root, year_level, class_name, subject, topic) based on the path.
        Gets the relevant piggymap from the path. (key = child content, value = dict with relevant child data + meta)
        """
        path = path.strip('/')

        template_type = get_template_from_path(path)
        metadata, segment = get_piggymap_segment_from_path(path, PIGGYMAP)

        media_abspath = f'/{MEDIA_ROUTE}/{path}' if path else f'/{MEDIA_ROUTE}'
        abspath = f'/{ASSIGNMENT_ROUTE}/{path}' if path else f'/{ASSIGNMENT_ROUTE}'

        return render_template(template_type,
                               meta=metadata,
                               segment=segment,
                               path=path,
                               media_abspath=media_abspath,
                               abspath=abspath)

    @assignment_routes.route(f'/<year_level>/<class_name>/<subject>/<topic>/<assignment>')
    def get_assignment(year_level, class_name, subject, topic, assignment, lang=''):
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

    @media_routes.route(f'/<path:wildcard>/media/<filename>')
    @assignment_routes.route(f'/<path:wildcard>/attachments/<filename>')
    def get_assignment_media_wildcard(wildcard, filename):
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
        # Generate a cache of all assignment related pages
        with app.app_context():
            cache_directory(PIGGYMAP, directory_fn=get_assignment_directory, assignment_fn=_render_assignment)

    app.register_blueprint(assignment_routes)
    app.register_blueprint(media_routes)

    return app
