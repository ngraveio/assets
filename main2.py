from src.core import Core

if __name__ == "__main__":
    Core.TrustWallet.build_json_from_trust_wallet_blockchains_dir(
        './src/input/blockchains',
        './src/output/assets.json'
    )
    Core.TrustWallet.build_new_folder_from_folder_and_json(
        './src/output/assets.json'
    )
    Core.merge_two_folders_into_one(
        './blockchains',
        './src/output/blockchains',
        './blockchains'
    )