# tests/test_auto_arrange.py

import unittest
import tempfile
import shutil
import os
import json
import auto_arrange
from src.config import AutoArrangeConfig
from PIL import Image


class TestAutoArrange(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Set up temporary input and output directories
        self.input_folder = os.path.join(self.temp_dir, "input")
        self.output_folder = os.path.join(self.temp_dir, "blockchains")
        os.makedirs(self.input_folder)
        os.makedirs(self.output_folder)

        # Create sample image files in the input directory
        for symbol in ["TT", "PALA", "CXKJ"]:
            img = Image.new("RGB", (100, 100))
            img_path = os.path.join(self.input_folder, f"{symbol.lower()}.png")
            img.save(img_path)

        # Create a mock assets.json file
        self.assets_info_file = os.path.join(self.temp_dir, "assets.json")
        with open(self.assets_info_file, "w") as f:
            json.dump(
                [
                    {"id": "thundertoken", "symbol": "TT", "name": "ThunderCore (TT)"},
                    {"id": "pala", "symbol": "PALA", "name": "Pala"},
                    {"id": "cxkj", "symbol": "CXKJ", "name": "CXKJ"},
                    {"id": "thundertoken@123123123", "symbol": "CXKJ", "name": "CXKJ"},
                    # Add other assets as needed
                ],
                f,
            )

        # Mock the config object
        auto_arrange.config.auto_arrange = AutoArrangeConfig(
            image_extensions=["png", "svg"],
            input_folder=self.input_folder,
            assets_info_file=self.assets_info_file,
            logo_name="logo",
            assets_folder="assets",
            output_folder=self.output_folder,
            supported_chain_ids=["thundertoken"],
        )

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.temp_dir)

    def test_auto_arrange(self):
        # Run the auto_arrange function
        auto_arrange.auto_arrange()

        import os

        # Check if the files are correctly arranged in the output folder
        for name in ["thundertoken", "Pala", "cxkj"]:
            output_path = os.path.join(self.output_folder, name, "logo.png")
            self.assertTrue(os.path.exists(output_path))

        # check of the token is correctly arranged in the assets folder
        token_coin_path = os.path.join(
            self.output_folder,
            "thundertoken",
            "assets",
            "123123123",
            "logo.png",
        )
        self.assertTrue(os.path.exists(token_coin_path))


if __name__ == "__main__":
    unittest.main()
