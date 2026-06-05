#!/bin/bash

# Ensure the directory exists
mkdir -p ~/Downloads/pictures

# Get source from argument, default to bing
SOURCE="${1:-bing}"
QUERY="${2:-}"
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
    if [ -n "$QUERY" ]; then
        CMD="$CMD --query \"$QUERY\""
    fi
fi

# Use NASA API key from environment variable if source is nasa
if [ "$SOURCE" == "nasa" ]; then
    if [ -n "$NASA_API_KEY" ]; then
        CMD="$CMD --api-key $NASA_API_KEY"
    fi
fi

# Use Flickr API key from environment variable if source is flickr
if [ "$SOURCE" == "flickr" ]; then
    if [ -z "$FLICKR_API_KEY" ]; then
        notify-send "Wallpaper Error" "FLICKR_API_KEY environment variable is not set"
        exit 1
    fi
    CMD="$CMD --flickr-api-key $FLICKR_API_KEY"
fi

# Run the command and check exit code
if eval $CMD '"$SOURCE"' '"$TARGET"'; then
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
