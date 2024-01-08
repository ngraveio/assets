from src.config import config
import glob
import os
from src.helper import is_png, is_svg
from cairosvg import svg2png


def convert_icons():
    for image in config.convert_icons.images:
        if is_svg(image.from_name) and is_png(image.to_name):
            for file in glob.glob(
                os.path.join(image.from_name),
                recursive=True,
            ):
                # get directory of file
                directory = os.path.dirname(file)
                svg2png(
                    url=file,
                    write_to=os.path.join(directory, image.to_name),
                    output_width=image.size,
                    output_height=image.size,
                )


if __name__ == "__main__":
    convert_icons()
