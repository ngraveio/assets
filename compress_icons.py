from src.config import config
from PIL import Image
import glob
import os


def compress_icons():
    for image in config.compress_icons.images:
        for file in glob.glob(
            image.from_name,
            recursive=True,
        ):
            # get directory of file
            directory = os.path.dirname(file)

            try:
                with Image.open(file) as img:
                    resized_img = img.resize(
                        (image.size, image.size), Image.Resampling.LANCZOS
                    )
                    resized_img.save(os.path.join(directory, image.to_name))
            except Exception:
                print(f"Failed to resize {file}")


if __name__ == "__main__":
    compress_icons()
