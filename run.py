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
    os.system(f"cd piggybank && git checkout {branch} && cd ..")


if __name__ == "__main__":
    from piggy.devtools import inject_devtools
    from piggy.piggybank import __update_piggymap

    # TODO: Re-enable
    checkout_branch("test-output")
    os.environ["FLASK_DEBUG"] = "1"
    os.environ["USE_CACHE"] = "0"

    app = create_app()
    inject_devtools(app)

    # Run node processes as subprocesses
    run_tailwind(reload=True)
    subprocess.Popen('npx livereload "piggy/, piggybank/"', shell=True)

    __update_piggymap()

    app.run(port=5001)
else:
    # TODO: Re-enable
    # checkout_branch("output")
    run_tailwind()  # Runs once to generate the CSS file
    app = create_app()
