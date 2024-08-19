import os

from piggy.app import create_app

if __name__ == '__main__':
    os.environ['FLASK_DEBUG'] = '1'
    # Disable LRU cache for development
    os.environ['USE_CACHE'] = '0'
    app = create_app()
    app.run(port=5001)
else:
    os.system('git submodule update --remote --recursive')
    app = create_app()
