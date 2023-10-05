#!/bin/bash



# Recursively find all directories
find ./blockchains/ethereum/assets -type d | while read -r dir; do
  # Convert the directory name to lowercase
  newdir=$(dirname "$dir")/$(basename "$dir" | tr '[:upper:]' '[:lower:]')
  
  # Check if the new name is different
  if [ "$dir" != "$newdir" ]; then
    # Rename the directory
    mv -v "$dir" "$newdir"
  fi
done