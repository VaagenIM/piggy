import atexit
import os
import subprocess

subprocesses = []


@atexit.register
def cleanup():
    print("\nSo long and thanks for all the fish!")
    for p in subprocesses:
        p.terminate()
        p.wait()


def run_tailwind(reload=False):
    cmd = f"cd piggy && npx tailwindcss -c tailwind.config.js -o static/css/tailwind.css {'--watch' if reload else ''} "
    subprocesses.append(subprocess.Popen(cmd, shell=True))


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
        subprocesses.append(subprocess.Popen("npx livereload 'piggy,piggybank' -e 'html,css,js,md'", shell=True))
        print("Houston, we have lift-off! (http://localhost:5001)")
    run_tailwind(reload=False)
    # Import after setting the environment variables for testing
    from piggy.app import create_app
    from piggy.devtools import inject_devtools

    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
    inject_devtools(app)

    app.run(port=5001)
else:
    # Production
    from piggy.app import create_app

    # TODO: Re-enable (requires branch to be published) (or a env to pass the branch with a PAT)
    # checkout_branch("output")
    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
