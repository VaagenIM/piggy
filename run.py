import os

from piggy.app import create_app

if __name__ == '__main__':
    os.system('cd piggybank && git checkout test-data && cd .. && git submodule update --remote --recursive')
    os.environ['FLASK_DEBUG'] = '1'
    os.environ['USE_CACHE'] = '0'
    app = create_app()
    app.run()
else:
    os.system('cd piggybank && git checkout output && cd .. && git submodule update --remote --recursive')
    app = create_app()
