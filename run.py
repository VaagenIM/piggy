import os
import subprocess

from piggy.app import create_app
from piggy.devtools import inject_devtools
from piggy.piggybank import __update_piggymap


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
    os.system(f"cd piggybank && git fetch && git checkout {branch} && git pull && cd ..")


if __name__ == "__main__":
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["USE_CACHE"] = "0"
    app = create_app()
    inject_devtools(app)
    __update_piggymap()
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        # This code will run only once, not in the reloaded processes
        checkout_branch("test-output")
        run_tailwind(reload=True)
        subprocess.Popen('npx livereload "piggy/, piggybank/"', shell=True)

    app.run(port=5001)
else:
    # TODO: Re-enable
    # checkout_branch("output")
    run_tailwind()  # Runs once to generate the CSS file
    app = create_app()
