#!/bin/bash

# 1. Define locations relative to the script
# The list file is in ../CGFNovelResults relative to where this script lives
LIST_FILE="../CGFNovelResults/filelist_novel.txt"
DEST_DIR="../CGFNovelResults/genomes"

# 2. Create the destination directory if it doesn't exist
if [ ! -d "$DEST_DIR" ]; then
    echo "Creating directory: $DEST_DIR"
    mkdir -p "$DEST_DIR"
fi

# 3. Check if the list file exists
if [ ! -f "$LIST_FILE" ]; then
    echo "Error: File list not found at $LIST_FILE"
    exit 1
fi

echo "Starting hardlink process..."

# 4. Read the file line by line and link
# We use a while loop to handle each line in the text file
while IFS= read -r SOURCE_PATH || [ -n "$SOURCE_PATH" ]; do
    
    # Skip empty lines
    if [ -z "$SOURCE_PATH" ]; then
        continue
    fi

    # Extract just the filename (e.g., GCA_025504455.1.fna.gz)
    FILENAME=$(basename "$SOURCE_PATH")
    
    # Check if the source file actually exists before linking
    if [ -f "$SOURCE_PATH" ]; then
        # Create the hardlink
        # Use -f to force overwrite if the link already exists (optional, safer to omit if you want to be warned)
        ln "$SOURCE_PATH" "$DEST_DIR/$FILENAME"
    else
        echo "Warning: Source file not found: $SOURCE_PATH"
    fi

done < "$LIST_FILE"

echo "Process complete. Files linked in $DEST_DIR"
