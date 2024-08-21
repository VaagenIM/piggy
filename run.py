import os
import subprocess
from piggy.app import create_app


def run_tailwind(reload=False):
    cmd = (
        "cd piggy && "
        f"npx tailwindcss {'--watch ' if reload else ''}"
        "-c tailwind.config.js "
        "-i static/css/tailwind.input.css "
        "-o static/css/tailwind.css && "
        "cd .."
    )
    subprocess.Popen(cmd, shell=True)


def checkout_branch(branch):
    os.system("git submodule update --init --recursive")
    os.system(f"cd piggybank && git checkout {branch} && cd .. && git submodule update --remote --recursive")


if __name__ == "__main__":
    # checkout_branch("test-output")
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["USE_CACHE"] = "0"
    os.environ["SERVER_NAME"] = "localhost:5001"
    app = create_app()
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    run_tailwind(reload=True)
    app.run(port=5001)
else:
    checkout_branch("output")
    run_tailwind()
    app = create_app()
