import atexit
import os
import subprocess
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

subprocesses = []

PORT = os.environ.get("PIGGY_PORT", 5001)
PIGGYBANK_DATA_URL = "https://github.com/VaagenIM/piggybank.git"
PIGGYBANK_DATA_FOLDER = Path("piggybank-data")


@atexit.register
def cleanup():
    print("\nSo long and thanks for all the fish!")
    for p in subprocesses:
        p.terminate()
        p.wait()


def checkout_branch():
    branch = os.environ.get("PIGGYBANK_BRANCH", "test-output")
    print("Checking out branch: " + branch)
    if "piggybank" in branch:
        cmd = f"cd piggybank && git fetch && git checkout {branch} --"
    else:
        cmd = f"cd piggybank && git stash && git fetch && git checkout {branch} && git pull"
    subprocess.run(cmd, shell=True, check=True)


def sync_piggybank_data():
    """Clone or update the latest UUID map from the piggybank data branch."""
    if not (PIGGYBANK_DATA_FOLDER / ".git").exists():
        if PIGGYBANK_DATA_FOLDER.exists():
            raise RuntimeError(f"{PIGGYBANK_DATA_FOLDER} exists but is not a git checkout")
        subprocess.run(
            ["git", "clone", "--branch", "data", "--single-branch", PIGGYBANK_DATA_URL, str(PIGGYBANK_DATA_FOLDER)],
            check=True,
        )
        return

    git = ["git", "-C", str(PIGGYBANK_DATA_FOLDER)]
    subprocess.run([*git, "fetch", "origin", "data"], check=True)
    subprocess.run([*git, "reset", "--hard", "origin/data"], check=True)


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
        checkout_branch()
        sync_piggybank_data()
        subprocesses.append(subprocess.Popen("npx livereload piggy,piggybank -e html,css,js,md", shell=True))
        print(f"Houston, we have lift-off! (http://localhost:{PORT})")
    # Import after setting the environment variables for testing
    from piggy.app import create_app
    from piggy.devtools import inject_devtools

    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
    inject_devtools(app)

    app.run(port=PORT)
else:
    # Production
    from piggy.app import create_app

    # TODO: Re-enable (requires branch to be published) (or a env to pass the branch with a PAT)
    # checkout_branch("output")
    app = create_app(debug=os.environ.get("FLASK_DEBUG", False) == "1")
