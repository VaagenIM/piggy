import re
from pathlib import Path

from enum import Enum

PIGGYBANK_FOLDER = Path("piggybank")

# A prefix for the assignment URLs, to avoid conflicts with other routes
ASSIGNMENT_ROUTE = "main"
# Media is on a different prefix to not compete with the assignment routes
MEDIA_ROUTE = "img"

ASSIGNMENTS_TEMPLATE_FOLDER = "assignments"
ASSIGNMENT_FILENAME_REGEX = re.compile(r"^(.+) Level (\d+) \- (.+).md$")


class AssignmentTemplate(Enum):
    ROOT = {"index": 0, "name": "assignments_root"}
    YEAR = {"index": 1, "name": "year_level"}
    CLASS = {"index": 2, "name": "class_name"}
    SUBJECT = {"index": 3, "name": "subject"}
    TOPIC = {"index": 4, "name": "topic"}
    ASSIGNMENT = {"index": 5, "name": "assignment"}

    @property
    def template(self):
        """Return the template path for the enum."""
        return f"{ASSIGNMENTS_TEMPLATE_FOLDER}/{self.value['index']}-{self.value['name']}.html"

    @property
    def index(self):
        """Return the index of the enum."""
        return self.value["index"]

    @staticmethod
    def get_template_from_index(index: int):
        """Return the template path for the index."""
        for v in AssignmentTemplate:
            if v.value["index"] == index:
                return v.template
        return None

    @staticmethod
    def get_dictmap():
        """Return a dictionary mapping the name to the index of the enum."""
        return {v.value["name"]: v.value["index"] for v in AssignmentTemplate}
