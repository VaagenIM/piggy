import os
from pathlib import Path

from flask import Flask, send_file, request, Blueprint, render_template
from flask_squeeze import Squeeze
from turtleconverter import generate_static_files
from werkzeug.middleware.proxy_fix import ProxyFix

from piggy import ASSIGNMENT_ROUTE, MEDIA_ROUTE, AssignmentTemplate, STATIC_FONTS_PATHS
from piggy.api import api_routes
from piggy.api import generate_thumbnail
from piggy.caching import cache_directory, _render_assignment_wildcard
from piggy.exceptions import PiggyHTTPException
from piggy.piggybank import generate_piggymap, get_piggymap_segment_from_path
from piggy.utils import normalize_path_to_str, lru_cache_wrapper, get_themes

# Ensure the working directory is the root of the project
os.chdir(os.path.dirname(Path(__file__).parent.absolute()))


# TODO: Logging


def create_app(debug: bool = False) -> Flask:
    app = Flask(__name__, static_folder="static")

    Squeeze().init_app(app)

    # TODO: add cache time to env (we use nginx caching for prod)
    default_cache_ttl = 86400 * 30 if debug else None  # 30 days
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = default_cache_ttl

    app.debug = debug

    # The following is necessary for the app to work behind a reverse proxy
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    assignment_routes = Blueprint(ASSIGNMENT_ROUTE, __name__, url_prefix=f"/{ASSIGNMENT_ROUTE}")
    media_routes = Blueprint(MEDIA_ROUTE, __name__, url_prefix=f"/{MEDIA_ROUTE}")

    generate_static_files(static_folder=Path(os.path.dirname(Path(__file__).absolute())) / "static")
    generate_piggymap()  # Generate the piggymap on startup (gets cached)

    use_github_pages = os.environ.get("GITHUB_PAGES", False)

    @app.context_processor
    def context_processor():
        """Context variables for all templates in the app."""
        return {
            "ASSIGNMENT_URL_PREFIX": ASSIGNMENT_ROUTE,
            "MEDIA_URL_PREFIX": MEDIA_ROUTE,
            "piggymap": generate_piggymap(),
            "img_fmt": "webp",
            "github_pages": use_github_pages,  # Used to determine if we should use lang in URL
            "AssignmentTemplate": AssignmentTemplate,
            "themes": get_themes(),
            "debug": app.debug,
            "static_fonts_paths": STATIC_FONTS_PATHS,
        }

    @app.template_global()
    @lru_cache_wrapper
    def get_template_name_from_index(i: int):
        """Return the template path for the index."""
        # Used to get the name of the template from the index via a path (breadcrumbs)
        return AssignmentTemplate.get_template_name_from_index(i - 1)

    @app.route("/")
    @lru_cache_wrapper
    def index():
        return render_template("index.html")

    @assignment_routes.route("/<path:path>")
    @assignment_routes.route("/")
    @lru_cache_wrapper
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
        try:
            return _render_assignment_wildcard(path, lang=lang)
        except PiggyHTTPException:
            return _render_assignment_wildcard(path, lang="")

    @assignment_routes.route("/<path:path>/lang/<lang>")
    @assignment_routes.route("/<path:path>/lang/")
    @lru_cache_wrapper
    def get_assignment_wildcard_lang(path, lang=""):
        """Only used when GitHub Pages is used to host the site."""
        return get_assignment_wildcard(path, lang)

    @media_routes.route("/<path:wildcard>/media/<path:filename>")
    @assignment_routes.route("/<path:wildcard>/attachments/<path:filename>")
    def get_assignment_media_wildcard(wildcard, filename):
        """
        Get a media file from either the media or attachments folder.
        (only in MEDIA_URL_PREFIX or ASSIGNMENT_URL_PREFIX)
        """

        # TODO: This might be slower than necessary, but the demanding fns are cached in the LRU cache
        #       (This fn cannot be cached as it handles files)

        if ["lang", "attachments"] == request.path.split("/")[-3:-1]:
            # If a language is specified, remove it from the wildcard (+ the assignment name)
            # This only happens when the language is specified in the URL and not via cookies
            wildcard = wildcard.rsplit("/", 2)[0]
        system_path = get_piggymap_segment_from_path(wildcard, generate_piggymap())[0].get("system_path", Path())
        if request.path.split("/")[1] == MEDIA_ROUTE:
            wildcard = wildcard.replace(MEDIA_ROUTE, "", 1).strip("/")
            folder = "media"
        else:
            folder = "attachments"
        try:
            return send_file(Path(system_path / folder / filename).absolute())
        except FileNotFoundError:
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
    if os.environ.get("USE_CACHE", "1") == "1":
        with app.app_context(), app.test_request_context():
            cache_directory(generate_piggymap(), fn=get_assignment_wildcard)

    # If GitHub pages is true, we create a .pid file to signal that the site is running
    # in a folder called gh-pages, which is the root of the GitHub Pages site
    if use_github_pages:
        os.makedirs("gh-pages", exist_ok=True)
        with open("gh-pages/.pid", "w+") as f:
            f.write(str(os.getpid()))

    return app
