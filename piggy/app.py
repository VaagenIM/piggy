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

print(PIGGYMAP)


def create_app():
    app = Flask(__name__, static_folder='static')
    generate_static_files()

    ASSIGNMENT_URL_PREFIX = 'oink'

    # TODO: None of this is sensible.
    # TODO: KeyError handler wrapper
    @app.route('/')
    @lru_cache()
    def index():
        html = '<h1>Velkommen til Piggy!</h1>'
        html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}"><button>Oppgaver</button></a>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}')
    @lru_cache()
    def assignments():
        html = '<h1>Oppgaver</h1>'
        for year in PIGGYMAP:
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{year}"><button>{year}</button></a>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>')
    @lru_cache()
    def year(year):
        html = f'<h1>{year}</h1>'
        for class_name in PIGGYMAP[year]['item']:
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{year}/{class_name}"><button>{class_name}</button></a>'
            for meta, val in PIGGYMAP[year]['item'][class_name]['meta'].items():  # Just a test
                html += f'\n<p>{meta}: {val}</p>'

        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>')
    @lru_cache()
    def class_name(year, class_name):
        html = f'<h1>{class_name}</h1>'
        for subject in PIGGYMAP[year]['item'][class_name]['item']:
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{year}/{class_name}/{subject}"><button>{subject}</button></a>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>/<subject>')
    @lru_cache()
    def subject(year, class_name, subject):
        html = f'<h1>{subject}</h1>'
        for topic in PIGGYMAP[year]['item'][class_name]['item'][subject]['item']:
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{year}/{class_name}/{subject}/{topic}"><button>{topic}</button></a>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>/<subject>/<topic>')
    @lru_cache()
    def topic(year, class_name, subject, topic):
        html = f'<h1>{topic}</h1>'
        for assignment in PIGGYMAP[year]['item'][class_name]['item'][subject]['item'][topic]['item'].values():
            html += f'\n<a href="/{ASSIGNMENT_URL_PREFIX}/{year}/{class_name}/{subject}/{topic}/{assignment["slug"]}"><button>{assignment["heading"]}</button></a>'
            for meta, val in assignment['meta'].items():
                html += f'\n<p>{meta}: {val}</p>'
        return html

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>/<subject>/<topic>/<assignment>')
    @lru_cache()
    def assignment(year, class_name, subject, topic, assignment):
        lang = request.args.get('lang', '')
        if lang:
            assignment = f'translations/{lang}/{assignment}'

        path = Path(f'{PIGGYBANK_FOLDER}/{year}/{class_name}/{subject}/{topic}/{assignment}.md')

        try:
            sections = mdfile_to_sections(path)
        except ConversionError:
            return 'Assignment not found', 404

        return render_template('oppgave.html', content=sections)

    @app.route(f'/{ASSIGNMENT_URL_PREFIX}/<year>/<class_name>/<subject>/<topic>/attachments/<attachment>')
    def attachments(year, class_name, subject, topic, attachment):
        try:
            path = Path(f'{PIGGYBANK_FOLDER}/{year}/{class_name}/{subject}/{topic}/attachments/{attachment}')
            return send_file(path)
        except FileNotFoundError:
            return 'Attachment not found', 404

    return app
