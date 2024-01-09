# tests/test_compress_icons.py

import unittest
import os
import shutil
import tempfile
from PIL import Image
import compress_icons
from src.config import CompressIconsConfig, CompressIconsConfigImage


class TestCompressIcons(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

        # Set up test configuration
        compress_icons.config.compress_icons = CompressIconsConfig(
            images=[
                CompressIconsConfigImage(
                    from_name=os.path.join(self.test_dir, "logo.png"),
                    to_name="logo64.png",
                    size=64,
                )
            ]
        )

        # Create a test image in the temporary directory
        test_image_path = os.path.join(self.test_dir, "logo.png")
        test_image = Image.new("RGB", (128, 128), color="red")
        test_image.save(test_image_path)

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def test_compress_icons_creates_logo64(self):
        # Run the compress_icons function
        compress_icons.compress_icons()

        # Check if the original and new files exist
        original_file = os.path.join(self.test_dir, "logo.png")
        new_file = os.path.join(self.test_dir, "logo64.png")
        self.assertTrue(os.path.exists(original_file))
        self.assertTrue(os.path.exists(new_file))
        self.assertNotEqual(os.path.getsize(original_file), os.path.getsize(new_file))


if __name__ == "__main__":
    unittest.main()
