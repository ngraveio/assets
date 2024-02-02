#!/bin/bash

# Usage: 
# 1. Install svgcleaner from the Github project
# https://github.com/RazrFalcon/svgcleaner
# 2. Add svgcleaner in $PATH by moving the binary inside
# /usr/local/bin for example.
# 3. Run the script 

# Iterate over all the blockchains
for file in blockchains/*/*.svg; do
    if [ -f "$file" ]; then
        echo "Trying to compress $file"
        svgcleaner $file $file
        echo "Compression complete for '$output_file'."
    fi
done

# Iterate over all the tokens
for file in blockchains/*/assets/*/*.svg; do
    if [ -f "$file" ]; then
    	echo "Trying to compress $file"
        svgcleaner $file $file
        echo "Compression complete for '$output_file'."
    fi
done

echo "Svg compression finished"
