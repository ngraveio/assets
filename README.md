# Assets

## Overview

Asset repository containing all the assets used in the project in both `.png` and `.svg` formats.

- [Assets](#assets)
  - [Overview](#overview)
  - [Adding coins to the repository](#adding-coins-to-the-repository)
  - [Config](#config)
    - [Options](#options)
    - [Example](#example)
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

[script.config.json](script.config.json) contains the configuration for the project.

### Options

| Key                                                     | Description                                               | Default Value            |
| ------------------------------------------------------- | --------------------------------------------------------- | ------------------------ |
| <span id="imageExtensions">`imageExtensions`</span>     | List of image extensions to be considered for the script. | `["png", "svg"]`         |
| <span id="inputFolder">`inputFolder`</span>             | Path to the input folder.                                 | `./input`                |
| <span id="assetsInfoFile">`assetsInfoFile`</span>       | Path to the assets info file.                             | `./assets.json`          |
| <span id="outputFolder">`outputFolder`</span>           | Path to the output folder.                                | `./blockchains`          |
| <span id="supportedChainIds">`supportedChainIds`</span> | List of supported chain ids.                              | `["ethereum", "elrond"]` |

### Example

example of the config file:

```json
{
  "imageExtensions": ["png", "svg"],
  "inputFolder": "./input",
  "assetsInfoFile": "./assets.json",
  "outputFolder": "./blockchains",
  "supportedChainIds": ["ethereum", "elrond"]
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
