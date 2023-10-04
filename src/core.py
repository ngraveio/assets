from .config import config
from .assets import Asset

class Core:
    @staticmethod
    def merge_two_folders_into_one(folder1: str, folder2: str, output_folder: str):
        import shutil, os
        
        # first copy folder1 to output_folder
        shutil.copytree(folder1, output_folder)
        
        # then copy folder2 to output_folder
        for dirpath, dirnames, filenames in os.walk(folder2):
            # Create any directories that don't already exist
            for dirname in dirnames:
                full_dirname = os.path.join(dirpath, dirname)
                rel_dir = os.path.relpath(full_dirname, folder2)
                dest_dir = os.path.join(output_folder, rel_dir)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            
            # Copy any files
            for filename in filenames:
                full_file_path = os.path.join(dirpath, filename)
                rel_path = os.path.relpath(full_file_path, folder2)
                dest_file_path = os.path.join(output_folder, rel_path)
                shutil.copy2(full_file_path, dest_file_path)
    # def merge_two_folders_into_one(folder1: str, folder2: str, output_folder: str):
    #     # first copy folder1 to output_folder
    #     import shutil, os
    #     shutil.copytree(folder1, output_folder)

    #     # then copy folder2 to output_folder
    #     # * all files in folder2 will overwrite files in output_folder if they have the same name or newly added if they are not in output_folder
    #     # * it is possible that some branches of folder2 are not in output_folder, so we need to create them and add from folder2

                

    class TrustWallet:
        BLOCKCHAINS_DIR = './src/input/blockchains'
        ASSETS_JSON = './src/output/assets.json'

        @staticmethod
        def build_new_folder_from_folder_and_json(assets_json: str = ASSETS_JSON):
            import os, json

            with open(assets_json, 'r') as f:
                assets = sorted(json.load(f), key=lambda x: "@" in x.get('id'))
                for asset in assets:
                    if (asset_id := asset.get('id')):
                        if "@" in asset_id:
                            coin_id, token_address = asset_id.split('@')
                            if coin_id not in config.supported_chain_ids:
                                continue
                        else:
                            coin_id = asset_id
                            token_address = None
                        print(os.path.join(asset.get('dir')), os.path.exists(asset_dir:=os.path.join(asset.get('dir'), 'logo.svg')), os.path.join(asset.get('dir'), 'logo.svg'), f'./src/output/blockchains/{coin_id}/{token_address}')
                        if token_address:
                            if os.path.exists(asset_dir:=os.path.join(asset.get('dir'), 'logo.svg')):
                                os.makedirs(f'./src/output/blockchains/{coin_id}/{token_address}', exist_ok=True)
                                os.rename(asset_dir, os.path.join(f'./src/output/blockchains/{coin_id}/{token_address}', 'logo.svg'))
                            if os.path.exists(asset_dir:=os.path.join(asset.get('dir'), 'logo.png')):
                                os.makedirs(f'./src/output/blockchains/{coin_id}/{token_address}', exist_ok=True)
                                os.rename(asset_dir, os.path.join(f'./src/output/blockchains/{coin_id}/{token_address}', 'logo.png'))                                
                        else:
                            if os.path.exists(asset_dir:=os.path.join(asset.get('dir'), 'logo.svg')):
                                os.makedirs(f'./src/output/blockchains/{coin_id}', exist_ok=True)
                                os.rename(asset_dir, os.path.join(f'./src/output/blockchains/{coin_id}', 'logo.svg'))
                            if os.path.exists(asset_dir:=os.path.join(asset.get('dir'), 'logo.png')):
                                os.makedirs(f'./src/output/blockchains/{coin_id}', exist_ok=True)
                                os.rename(asset_dir, os.path.join(f'./src/output/blockchains/{coin_id}', 'logo.png'))

        @staticmethod
        def build_json_from_trust_wallet_blockchains_dir(blockchains_dir: str = BLOCKCHAINS_DIR, assets_json: str = ASSETS_JSON):
            import os, json

            assets = []
            paths = []

            for root, dirs, files in os.walk(blockchains_dir):
                for file in files:
                    if file.lower().endswith('.json'):
                        json_file_path = os.path.join(root, file)
                        paths.append(json_file_path)
                        with open(json_file_path, 'r') as f:
                            json_data = json.load(f)
                            parts = json_file_path.replace(blockchains_dir + "/", "").split('/')
                            print(parts)
                            if (type(json_data) == list): 
                                continue
                            if len(parts) == 4:
                                coin_id = parts[0]
                                address = parts[2]
                                assets.append({
                                    'id': "{}@{}".format(coin_id, address),
                                    'symbol': json_data.get('symbol'),
                                    "name": json_data.get('name'),
                                    "dir": os.path.dirname(json_file_path),
                                })
                            elif len(parts) == 3 and parts[1] == 'info':
                                id = parts[0]
                                assets.append({
                                    'id': id,
                                    'symbol': json_data.get('symbol'),
                                    "name": json_data.get('name'),
                                    "dir": os.path.dirname(json_file_path),
                                })
            # return assets
            # save json file
            with open(assets_json, 'w') as f:
                json.dump(assets, f, indent=4)

            # # save paths file
            # with open('paths.json', 'w') as f:
            #     json.dump(paths, f, indent=4)