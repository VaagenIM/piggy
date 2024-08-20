import os
import subprocess

from piggy.app import create_app

TAILWIND_RUN_CMD = ('cd piggy && '
                    'npx tailwindcss -c tailwind.config.js '
                    '-i static/css/tailwind.input.css '
                    '-o static/css/tailwind.css && '
                    'cd ..')

subprocess.Popen(TAILWIND_RUN_CMD, shell=True)


def checkout_branch(branch):
    os.system(f'cd piggybank && git checkout {branch} && cd .. && git submodule update --remote --recursive')


if __name__ == '__main__':
    # checkout_branch('test-data')
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['USE_CACHE'] = '0'
    app = create_app()
    app.run(port=5001)
else:
    checkout_branch('output')
    app = create_app()
