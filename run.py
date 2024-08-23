import os
import subprocess

from piggy.app import create_app


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
    os.system("git submodule update --init --recursive")
    os.system(f"cd piggybank && git checkout {branch} && cd .. && git submodule update --remote --recursive")


if __name__ == "__main__":
    from livereload import Server
    from piggy.devtools import inject_devtools

    # checkout_branch("test-output")
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["USE_CACHE"] = "0"

    app = create_app()

    if not os.environ.get("injected", False):
        inject_devtools(app)

    os.environ["injected"] = "1"

    run_tailwind(reload=True)

    """
    server = Server(app)
    server.watch("piggy/**/*", ignore=lambda *_: False)
    server.watch("piggybank/*", ignore=lambda *_: False)
    server.serve(host="127.0.0.1", port=5001, debug=False)
    """

    app.run(port=5001)
else:
    checkout_branch("output")
    run_tailwind()
    app = create_app()
