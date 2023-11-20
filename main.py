from src.assets import AssetItems, Asset
from src.config import config
import os

asset_items = AssetItems(config.assets_info_file)
assets = []

for root, dirs, files in os.walk(config.input_dir):
    for file in files:
        if any(file.lower().endswith(f".{ext}") for ext in config.image_extensions):
            icon_name = os.path.join(root, file)
            symbol = Asset.get_symbol_from_icon_name(icon_name)

            asset_items_by_symbol = asset_items.get_assets_by_symbol(symbol)
            if not asset_items_by_symbol: 
                print(f'No asset found for symbol {symbol}')
                continue
            len(asset_items_by_symbol) > 1 and print(f'Found multiple assets for symbol {symbol}')
            assets_of_symbol = filter(lambda asset: not asset.is_token or asset.parent_id in config.supported_chain_ids, (Asset(asset_item, icon_name) for asset_item in asset_items_by_symbol))
            assets.extend(assets_of_symbol)

assets.sort(key=lambda x: x.is_token)

for asset in assets:
    asset.save()

for asset in assets:
    if asset.is_saved and os.path.exists(asset.icon):
        os.remove(asset.icon)
