from typing import TypedDict
import json

class Config:
    def __init__(self, path: str) -> None:
        with open(path, 'r') as f:
            self._config = json.load(f)
        
        self.input_dir: str = self._config['inputFolder']
        self.image_extensions: list[str] = self._config['imageExtensions']
        self.assets_info_file: str = self._config['assetsInfoFile']
        self.blockchains_folder: list[str] = self._config['outputFolder']
        self.assets_folder: str = self._config['assetsFolder']
        self.logo_name: str = self._config['logoName']
        self.supported_chain_ids: str = self._config['supportedChainIds']
    
config = Config('./script.config.json')