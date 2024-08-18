import os

from piggy.app import create_app

if __name__ == '__main__':
    os.environ['FLASK_DEBUG'] = '1'
    # Disable LRU cache for development
    os.environ['USE_CACHE'] = '0'
    app = create_app()
    app.run()
else:
    app = create_app()
