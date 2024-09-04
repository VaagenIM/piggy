import os
import subprocess


def run_tailwind(reload=False):
    cmd = (
        "cd piggy && "
        f"npx tailwindcss {'--watch' if reload else ''}"
        "-c tailwind.config.js "
        "-i static/css/tailwind.input.css "
        "-o static/css/tailwind.css && "
        "cd .."
    )
    subprocess.Popen(cmd, shell=True)


def checkout_branch(branch):
    os.system(f"cd piggybank && git stash && git fetch && git checkout {branch} && git pull && cd ..")


if __name__ == "__main__":
    # Debug
    import logging

    # Reduce the amount of logging from werkzeug
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)

    # Set the environment variables for testing
    os.environ["USE_CACHE"] = "0"
    os.environ["FLASK_DEBUG"] = "1"

    # Run these once on the first run
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # This code will run only once, not in the reloaded processes
        checkout_branch("test-output")
        run_tailwind(reload=True)  # TODO: This does not keep watching for changes
        subprocess.Popen('npx livereload "piggy/, piggybank/"', shell=True)
        print("Houston, we have lift-off! (http://localhost:5001)")

    # Import after setting the environment variables for testing
    from piggy.app import create_app
    from piggy.devtools import inject_devtools
    from piggy.piggybank import __update_piggymap

    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
    inject_devtools(app)  # Inject devtools
    __update_piggymap()  # Run on every reload

    app.run(port=5001)
else:
    # Production
    from piggy.app import create_app

    # TODO: Re-enable (requires branch to be published) (or a env to pass the branch with a PAT)
    # checkout_branch("output")
    run_tailwind()  # Runs once to generate the CSS file
    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
