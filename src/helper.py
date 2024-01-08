import os
from typing import Generator


def get_files(folder) -> Generator[str, None, None]:
    return (
        os.path.join(root, file)
        for root, dirs, files in os.walk(folder)
        for file in files
    )


def is_svg(file):
    return file.lower().endswith(".svg")


def is_png(file):
    return file.lower().endswith(".png")
