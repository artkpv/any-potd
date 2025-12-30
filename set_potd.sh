#!/bin/bash

# Ensure the directory exists
mkdir -p ~/Downloads/pictures

# Get source from argument, default to bing
SOURCE="${1:-bing}"
TARGET="$HOME/Downloads/pictures/${SOURCE}-potd.jpg"

# Prepare python command
CMD="/usr/bin/python3 $HOME/code/any-photo-of-the-day/any_potd.py"

# Use Unsplash API key from environment variable if source is unsplash
if [ "$SOURCE" == "unsplash" ]; then
    if [ -z "$UNSPLASH_API_KEY" ]; then
        notify-send "Wallpaper Error" "UNSPLASH_API_KEY environment variable is not set"
        exit 1
    fi
    CMD="$CMD --unsplash-api-key $UNSPLASH_API_KEY"
fi

# Run the command
$CMD "$SOURCE" "$TARGET"

# Check if download was successful
if [ -f "$TARGET" ]; then
    # Resize the image to 1920x1080 (fill) without distortion using magick
    magick "$TARGET" -resize 1920x1080^ -gravity center -extent 1920x1080 "$TARGET"

    # Create a symlink to the last downloaded image
    SYMLINK="$HOME/Downloads/pictures/last-potd.jpg"
    ln -sf "$TARGET" "$SYMLINK"

    # Set wallpaper using the symlink
    feh --no-fehbg --bg-fill "$SYMLINK"
else
    notify-send "Wallpaper Update" "Failed to download image from $SOURCE"
fi