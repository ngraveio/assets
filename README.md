# Assets

## Setup

1. Install [python3](https://www.python.org/downloads/) on your system.
2. Install [pip](https://pip.pypa.io/en/stable/installing/) on your system.
3. run `python -m venv venv` to create a virtual environment
4. run `source venv/bin/activate` to activate the virtual environment
5. run `pip install -r requirements.txt` to install all the dependencies
6. run `deactivate` to deactivate the virtual environment
7. Optional: you can install recommended extensions for VSCode from [.vscode/extensions.json](.vscode/extensions.json)

## Overview

Asset repository containing all the assets used in the project in both `.png` and `.svg` formats.

- [Assets](#assets)
  - [Setup](#setup)
  - [Overview](#overview)
  - [Adding coins to the repository](#adding-coins-to-the-repository)
  - [Config](#config)
    - [Auto Arrange Icons (auto_arrange)](#auto-arrange-icons-auto_arrange)
      - [Options](#options)
      - [Example](#example)
    - [Compress Existing Icons (compress_icons)](#compress-existing-icons-compress_icons)
      - [Options](#options-1)
      - [Example](#example-1)
    - [Convert icons to different formats (convert_icons)](#convert-icons-to-different-formats-convert_icons)
      - [Options](#options-2)
      - [Example](#example-2)
  - [Add new icon](#add-new-icon)
    - [Pre-requisites](#pre-requisites)
    - [Steps](#steps)
    - [Output](#output)

## Adding coins to the repository

There are options:

1. Using the script to add icons. You can see configuration options below.
   - add icons to input folder
   - run the script
   - if some icons are not added, probably assets.json misses info about icon
   - add missing icons to assets.json and rerun the script
2. Manual adding of icons
   - Create the correct folder structure
   - Add each icon manually

## Config

[script.config.json](script.config.json) contains the configuration for the project scripts.

### Auto Arrange Icons (auto_arrange)

#### Options

| Key                   | Description                                                                           | Example Value            |
| --------------------- | ------------------------------------------------------------------------------------- | ------------------------ |
| `image_extensions`    | List of image extensions to be considered by the script.                              | `["png", "svg"]`         |
| `input_folder`        | Path to the input folder.                                                             | `input`                  |
| `assets_info_file`    | Path to the assets info file.                                                         | `assets.json`            |
| `logo_name`           | Specifies the name of icons after they're arranged to the right destination (folder). | `logo`                   |
| `assets_folder`       | Path to the folder where tokens of the coins should be kept.                          | `assets`                 |
| `output_folder`       | Path to the output folder that will contain all the icons of the assets               | `blockchains`            |
| `supported_chain_ids` | Chain ids that are currently supported                                                | `["ethereum", "elrond"]` |

#### Example

example of the config file:

```json
{
  "auto_arrange": {
    "image_extensions": ["png", "svg"],
    "input_folder": "input",
    "assets_info_file": "assets.json",
    "logo_name": "logo",
    "assets_folder": "assets",
    "output_folder": "blockchains",
    "supported_chain_ids": ["ethereum", "elrond"]
  }
  // ... other configs
}
```

<span id="structure-example">example above results in the following output:</span>

```bash
% python3 auto_arrange.py
% tree blockchains
blockchains
├── ethereum
│   ├── logo.png
│   ├── logo.svg
│   ├── assets
│   │   ├── 0x0bc529c00c6401aef6d220be8c6ea1667f6ad93e
│   │   │   ├── logo.png
│   │   │   └── logo.svg
│   │   ├── 0x0c10bf8fcb7bf5412187a595ab97a3609160b5c6
│   │   │   ├── logo.png
.   .   .   └── logo.svg
.   .   .
```

### Compress Existing Icons (compress_icons)

#### Options

| Key                  | Description                                                               | Example Value               |
| -------------------- | ------------------------------------------------------------------------- | --------------------------- |
| `images[].from_name` | name of the source icon that needs to be resized                          | `./blockchains/**/logo.svg` |
| `images[].to_name`   | name of the resized icon (it is placed in the same folder as source icon) | `logo.png`                  |
| `images[].size`      | desired size of the icon after resizing                                   | `256`                       |

#### Example

example of the config file:

```json
{
  "compress_icons": {
    "images": [
      {
        "from_name": "./blockchains/**/logo.png",
        "to_name": "logo64.png",
        "size": 64
      }
    ]
  }
  // ... other configs
}
```

### Convert icons to different formats (convert_icons)

#### Options

| Key                  | Description                                                           | Example Value               |
| -------------------- | --------------------------------------------------------------------- | --------------------------- |
| `images[].from_name` | name of the source icon that needs to be converted                    | `./blockchains/**/logo.svg` |
| `images[].to_name`   | name of the converted icon (placed in the same folder as source icon) | `logo.png`                  |

#### Example

example of the config file:

```json
{
  "convert_icons": {
    "images": [
      {
        "from_name": "./blockchains/**/logo.svg",
        "to_name": "logo.png"
      }
    ]
  }
  // ... other configs
}
```

## Add new icon

#### Pre-requisites

- [python3](https://www.python.org/downloads/) installed on your system.

#### Steps

1. Put any folder of any structure in the [input](#inputFolder) folder containing the icons.
2. Open terminal in the root of the project and run the following command:

```bash
% python3 auto_arrange.py
```

#### Output

- [output](#outputFolder) folder will be created in the root of the project if not already present.
- All the image files will be moved to the output folder of the [desired structure](#structure-example).
