import os
from pathlib import Path

from flask import Flask, send_file, request, Blueprint, render_template
from turtleconverter import generate_static_files

from piggy import PIGGYBANK_FOLDER, ASSIGNMENT_ROUTE, MEDIA_ROUTE, AssignmentTemplate
from piggy.api import api_routes
from piggy.api import generate_thumbnail
from piggy.caching import lru_cache_wrapper, _render_assignment, cache_directory, _render_assignment_wildcard
from piggy.exceptions import PiggyHTTPException
from piggy.piggybank import PIGGYMAP
from piggy.utils import normalize_path_to_str

# Ensure the working directory is the root of the project
os.chdir(os.path.dirname(Path(__file__).parent.absolute()))


# TODO: Logging


def create_app():
    app = Flask(__name__, static_folder="static")

    assignment_routes = Blueprint(ASSIGNMENT_ROUTE, __name__, url_prefix=f"/{ASSIGNMENT_ROUTE}")
    media_routes = Blueprint(MEDIA_ROUTE, __name__, url_prefix=f"/{MEDIA_ROUTE}")

    generate_static_files(static_folder=os.path.dirname(Path(__file__).absolute()) + "/static")

    use_github_pages = os.environ.get("GITHUB_PAGES", False)

    @app.context_processor
    def context_processor():
        """Context variables for all templates in the app."""
        return {
            "ASSIGNMENT_URL_PREFIX": ASSIGNMENT_ROUTE,
            "MEDIA_URL_PREFIX": MEDIA_ROUTE,
            "piggymap": PIGGYMAP,
            "img_fmt": "webp",
            "github_pages": use_github_pages,  # Used to determine if we should use lang in URL
        }

    @app.route("/")
    @lru_cache_wrapper
    def index():
        return render_template("index.html")

    @assignment_routes.route("/<path:path>")
    @assignment_routes.route("/")
    def get_assignment_wildcard(path="", lang=""):
        path = path.strip("/")
        path = normalize_path_to_str(path, replace_spaces=True)

        # If we are over the final level (assignment), raise a 404
        if len(path.split("/")) > AssignmentTemplate.ASSIGNMENT.index:
            raise PiggyHTTPException("Assignment not found", status_code=404)

        # If we are at the final level (assignment), get lang from the cookies (valid requests only)
        if len(path.split("/")) == AssignmentTemplate.ASSIGNMENT.index and request and not lang:
            lang = request.cookies.get("lang", "")  # "" = default language (Norwegian

        # Render the appropriate template for the current level
        return _render_assignment_wildcard(path, lang=lang)

    @assignment_routes.route("/<path:path>/lang/<lang>")
    @assignment_routes.route("/<path:path>/lang/")
    def get_assignment_wildcard_lang(path, lang=""):
        """Only used when GitHub Pages is used to host the site."""
        return get_assignment_wildcard(path, lang)

    @media_routes.route("/<path:wildcard>/media/<filename>")
    @assignment_routes.route("/<path:wildcard>/attachments/<filename>")
    def get_assignment_media_wildcard(wildcard, filename):
        """
        Get a media file from either the media or attachments folder.
        (only in MEDIA_URL_PREFIX or ASSIGNMENT_URL_PREFIX)
        """
        if ["lang", "attachments"] == request.path.split("/")[-3:-1]:
            # If a language is specified, remove it from the wildcard (+ the assignment name)
            # This only happens when the language is specified in the URL and not via cookies
            wildcard = wildcard.rsplit("/", 2)[0]
        if request.path.split("/")[1] == MEDIA_ROUTE:
            wildcard = wildcard.replace(MEDIA_ROUTE, "", 1).strip("/")
            folder = "media"
        else:
            folder = "attachments"
        try:
            return send_file(Path(f"{PIGGYBANK_FOLDER}/{wildcard}/{folder}/{filename}").absolute())
        except FileNotFoundError:
            # TODO: This is a long method. Refactor to a separate function
            if folder == "media":
                # if there is no /, we are at the root folder and should repeat the name
                _, name = wildcard.rsplit("/", 1) if "/" in wildcard else (wildcard, wildcard)
                query_params = {"c": name, "width": 1024, "height": 512}
                return generate_thumbnail(name, request=request.from_values(query_string=query_params))
            return send_file("static/img/placeholders/100x100.png")

    app.register_blueprint(assignment_routes)
    app.register_blueprint(media_routes)
    app.register_blueprint(api_routes)

    # Cache all assignment related pages if not in debug mode
    if not app.debug:
        with app.app_context(), app.test_request_context():
            cache_directory(PIGGYMAP, directory_fn=_render_assignment_wildcard, assignment_fn=_render_assignment)

    return app
