#!/bin/bash

# Usage: 
# 1. Install svgcleaner from the Github project
# https://github.com/RazrFalcon/svgcleaner
# 2. Add svgcleaner in $PATH by moving the binary inside
# /usr/local/bin for example.
# 3. Install optipng with apt
# 4. Run the script 

# Iterate over svg files
for file in blockchains/*/*.svg blockchains/*/assets/*/*.svg; do
    if [ -f "$file" ]; then
        echo "Trying to compress $file"
        svgcleaner $file $file
        echo "Compression complete for '$file'."
    fi
done

# Iterate over png files
for file in blockchains/*/*.png blockchains/*/assets/*/*.png; do
    if [ -f "$file" ]; then
        echo "Trying to compress $file"
        optipng $file $file
        echo "Compression complete for '$file'."
    fi
done

echo "All images have been compressed"
