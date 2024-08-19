import os
from pathlib import Path

from turtleconverter import generate_static_files


def generate_static_files_wrapper():
    cwd = os.getcwd()
    os.chdir(os.path.dirname(Path(__file__).absolute()))
    generate_static_files()
    os.chdir(cwd)
