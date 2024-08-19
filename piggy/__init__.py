from pathlib import Path

from piggy.piggybank import generate_piggymap

PIGGYBANK_FOLDER = Path('piggybank')
PIGGYMAP = generate_piggymap(PIGGYBANK_FOLDER)

SUPPORTED_LANGUAGES = {
    '': {'name': 'Norsk'},  # Default language
    'eng': {'name': 'English'},
    'ukr': {'name': 'Українська'},
}

# A prefix for the assignment URLs, to avoid conflicts with other routes
ASSIGNMENT_ROUTE = 'main'
# Media is on a different prefix to not compete with the assignment routes
MEDIA_ROUTE = 'img'
