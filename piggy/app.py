import os
from glob import glob
from pathlib import Path

from flask import Flask, render_template, send_file
from turtleconverter import mdfile_to_sections, generate_static_files

# Change working directory to the directory of this file so that we can use relative paths
os.chdir(os.path.dirname(__file__))

ASSIGNMENTS_FOLDER = '../assignments/'
MEDIA_FORMATS = ['png', 'jpg', 'jpeg', 'gif']
CLASSES = [subject for subject in os.listdir(ASSIGNMENTS_FOLDER)]


def get_assignments_by_subject(class_name: str):
    # TODO: make this more sensible!
    assignments = []
    for md_file in glob(f'{ASSIGNMENTS_FOLDER}/{class_name}/*/*.md'):
        path, filename = os.path.split(md_file[len(ASSIGNMENTS_FOLDER):])
        assignments.append({
            'path': Path(path[1:]).as_posix(),
            'subject': Path(md_file).parent.name,
            'name': filename.replace('.md', '')
        })

    return assignments


def is_media_format(path: Path):
    return path.suffix[1:].lower() in MEDIA_FORMATS


def create_app():
    app = Flask(__name__, static_folder='static')
    generate_static_files()

    @app.route('/')
    def index():
        # TODO: make this readable!
        html = '<h1>Assignments</h1>'
        html += ''.join([''.join([
            f'{class_name} | {assignment["subject"]} - <a href="/{assignment["path"]}/{assignment["name"]}">{assignment["name"]}</a><br>'
            for assignment in get_assignments_by_subject(class_name)])
            for class_name in CLASSES])
        return html

    # Construct routes for each class/subject
    for class_name in CLASSES:
        def class_route(class_name, path):
            # TODO: Put this in a wrapper?
            file = Path(f'{ASSIGNMENTS_FOLDER}/{class_name}/{path}')
            if not file.suffix:
                file = Path(f'{file}.md')
            if not file.exists():
                return 'File not found', 404
            if is_media_format(file):
                return send_file(file)

            return render_template('oppgave.html',
                                   content=mdfile_to_sections(file))

        app.add_url_rule(f'/{class_name}/<path:path>', f'{class_name}_route',
                         lambda path, _class_name=class_name: class_route(class_name, path))
    return app
