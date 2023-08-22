
from typing import TypedDict
from .config import config
from json import load
import shutil
import os

class AssetItem(TypedDict):
    id: str
    symbol: str
    name: str

class AssetItems:
    def __init__(self, path: str) -> None:
        with open(path, 'r') as f:
            self._assets: list[AssetItem] = load(f)
        
        self._symbol_to_asset: dict[str, list[AssetItem]] = {}

        for asset in self._assets:
            if asset["symbol"]:
                asset["symbol"] = asset["symbol"].lower()
                if asset['symbol'] not in self._symbol_to_asset:
                    self._symbol_to_asset[asset['symbol']] = []
                self._symbol_to_asset[asset['symbol']].append(asset)
    
    def get_assets_by_symbol(self, symbol: str):
        return self._symbol_to_asset.get(symbol)

class Asset:
    def __init__(self, asset_item: AssetItem, icon:str) -> None:
        self._asset_item = asset_item
        self.name = asset_item["name"]
        self.symbol = asset_item["symbol"]
        self.id = asset_item["id"]
        self.icon = icon
        self.is_saved = False

    @property
    def icon_extension(self):
        return self.icon.split('.')[-1]

    @staticmethod
    def get_symbol_from_icon_name(icon: str):
        return icon.split('/')[-1].split('.')[0].lower()
    
    @property
    def is_token(self):
        return "@" in self.id
    
    @property
    def address(self):
        return self.id.split('@')[1]
    
    @property
    def parent_id(self):
        return self.id.split('@')[0]

    def __str__(self) -> str:
        return self.icon
    
    def __repr__(self) -> str:
        return self.icon
    
    def save(self):
        if self.is_token:
            os.makedirs(f'{config.blockchains_folder}/{self.parent_id}/{config.assets_folder}/{self.address}', exist_ok=True)
            shutil.copyfile(self.icon, f'{config.blockchains_folder}/{self.parent_id}/{config.assets_folder}/{self.address}/{config.logo_name}.{self.icon_extension}')
            self.is_saved = True
        else:
            os.makedirs(f'{config.blockchains_folder}/{self.id}', exist_ok=True)
            shutil.copyfile(self.icon, f'{config.blockchains_folder}/{self.id}/{config.logo_name}.{self.icon_extension}')
            self.is_saved = True
            
            
