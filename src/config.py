from typing import List
import json
from pydantic import BaseModel


class AutoArrangeConfig(BaseModel):
    input_folder: str
    image_extensions: List[str]
    assets_info_file: str
    output_folder: str
    assets_folder: str
    logo_name: str
    supported_chain_ids: List[str]


class CompressIconsConfigImage(BaseModel):
    from_name: str
    to_name: str
    size: int


class ConvertIconsConfigImage(BaseModel):
    from_name: str
    to_name: str


class CompressIconsConfig(BaseModel):
    images: List[CompressIconsConfigImage]


class ConvertIconsConfig(BaseModel):
    images: List[ConvertIconsConfigImage]


class Config(BaseModel):
    auto_arrange: AutoArrangeConfig
    compress_icons: CompressIconsConfig
    convert_icons: ConvertIconsConfig


with open("./script.config.json", "r") as f:
    config = Config(**json.load(f))
