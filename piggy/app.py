import os
from functools import lru_cache
from pathlib import Path

from flask import Flask, send_file, request, render_template
from turtleconverter import generate_static_files, mdfile_to_sections, ConversionError

from piggy.piggybank import generate_piggymap

# Change working directory to the directory of this file so that we can use relative paths
os.chdir(os.path.dirname(__file__))

PIGGYBANK_FOLDER = Path('../piggybank')
PIGGYMAP = generate_piggymap(PIGGYBANK_FOLDER)

SUPPORTED_LANGUAGES = {
    '': {'name': 'Norsk'},
    'eng': {'name': 'English'},
    'ukr': {'name': 'Українська'},
}


def get_piggymap_segment_from_uri(uri: str) -> dict or None:
    """Get the piggymap from a URI."""
    piggymap = dict(PIGGYMAP)
    for path in uri.split('/'):
        if not path:
            continue
        if path not in piggymap:
            return None
        piggymap = piggymap.get(path, {}).get('data', {})
    return piggymap


def get_directory_name_from_uri(uri: str) -> str:
    """Get the directory name from a URI."""
    # TODO: Use an enum?
    nest_level_dirname = {
        0: 'assignments_root',
        1: 'year_level',
        2: 'class_name',
        3: 'subject',
        4: 'topic',
    }
    uri = uri.split('/')
    return nest_level_dirname.get(len([x for x in uri if x]), 'unknown')


def create_app():
    app = Flask(__name__, static_folder='static')
    generate_static_files()

    # A prefix for the assignment URLs, to avoid conflicts with other routes
    ASSIGNMENT_URL_PREFIX = 'main'
    # We can't have the media files have the same URL prefix as the assignments, as it would conflict
    # with the wildcard route for the media files.
    MEDIA_URL_PREFIX = 'img'

    @app.route('/')
    @lru_cache
    def index():
        html = '<h1>Velkommen til Piggy!</h1>'
        html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}"><button>Oppgaver</button></a>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<path:uri>')
    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/')
    @lru_cache
    def render_assignment_directories(uri=''):
        """
        Render the webpage for a given URI.

        Keeps track of template_type (assignments_root, year_level, class_name, subject, topic) based on the URI.
        Gets the relevant piggymap from the URI. (key = child content, value = dict with relevant child data + meta)
        """
        uri = uri.strip('/')

        template_type = get_directory_name_from_uri(uri)

        # We can use the data to display the content on the webpage in the correct context
        # We can use piggymap to generate different kinds of content based on the URI
        # TODO:
        # return render_template(f'{template_type}.html', data=get_piggymap_segment_from_uri(uri), piggymap=PIGGYMAP)

        html = f'<h1>{template_type}</h1>'
        for key, val in get_piggymap_segment_from_uri(uri).items():
            print('key:', key)
            print('val:', val)

            img_url = f'/{MEDIA_URL_PREFIX}/{uri}/{key}/media/header.png'
            html += f'<img src="{img_url}">'
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{uri}/{key}"><button>{key}</button></a>'
            for meta_key, meta_val in val.get('meta', {}).items():
                html += f'\n<p>{meta_key}: {meta_val}</p>'
        return html

    assignment_cache = {}

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>/<subject>/<topic>/<assignment>')
    # Uses its own cache
    def render_assignment(year, class_name, subject, topic, assignment):
        """
        Render an assignment from the piggymap. Takes precedence over the wildcard route due to specificity.
        """
        lang = ''
        if request:
            lang = request.cookies.get('lang')
        if lang:
            assignment = f'translations/{lang}/{assignment}'

        path = Path(f'{PIGGYBANK_FOLDER}/{year}/{class_name}/{subject}/{topic}/{assignment}.md')

        # If the assignment has already been rendered, we can just return that
        if path in assignment_cache:
            return assignment_cache[path]

        try:
            sections = mdfile_to_sections(path)
        except ConversionError:
            # TODO: If the assignment exists but the translation is missing, we should show a message to the user
            #       and allow them to change the language.
            output = 'Translation not found', 404
            assignment_cache[path] = output
            return output

        final_render = render_template('oppgave.html',
                                       content=sections,
                                       current_language=SUPPORTED_LANGUAGES.get(lang, {}).get('name', 'Unknown'),
                                       supported_languages=SUPPORTED_LANGUAGES)
        assignment_cache[path] = final_render
        print('Assignment rendered:', path)
        return final_render

    def cache_all_assignments():
        """Reduces load time by caching all assignments on startup."""
        with app.app_context():
            for year, year_data in PIGGYMAP.items():
                for class_name, cls, in year_data.get('data', {}).items():
                    for subject, subject_data in cls.get('data', {}).items():
                        for topic, topic_data in subject_data.get('data', {}).items():
                            for assignment, assignment_data in topic_data.get('data', {}).items():
                                render_assignment(year, class_name, subject, topic, assignment)
                                for lang in SUPPORTED_LANGUAGES.keys():
                                    render_assignment(year, class_name, subject, topic,
                                                      f'translations/{lang}/{assignment}')

    @app.route(f'/{MEDIA_URL_PREFIX}/<path:wildcard>/media/<filename>')
    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<path:wildcard>/attachments/<filename>')
    def get_media_wildcard(wildcard, filename):
        """
        Get a media file from either the media or attachments folder.
        (only in MEDIA_URL_PREFIX or ASSIGNMENT_URL_PREFIX)
        """
        if request.path.split('/')[1] == MEDIA_URL_PREFIX:
            wildcard = wildcard.replace(MEDIA_URL_PREFIX, '', 1).strip('/')
            folder = 'media'
        else:
            folder = 'attachments'
        try:
            return send_file(Path(f'{PIGGYBANK_FOLDER}/{wildcard}/{folder}/{filename}'))
        except FileNotFoundError:
            return send_file('static/img/placeholders/100x100.png')

    cache_all_assignments()

    return app
