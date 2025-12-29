#!/usr/bin/env python3
"""
any-photo-of-the-day: Download photo of the day from various sources

Supported sources:
- bing: Bing Photo of the Day
- nasa: NASA Astronomy Picture of the Day (APOD)
- natgeo: National Geographic Photo of the Day
- unsplash: Unsplash random photos (with optional topics)
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests


# Global verbose flag
VERBOSE = False


def log_verbose(message: str):
    """Print message if verbose mode is enabled"""
    if VERBOSE:
        print(f"[INFO] {message}")


def retry_request(url: str, max_retries: int = 3, timeout: int = 30, headers: Optional[dict] = None, params: Optional[dict] = None) -> requests.Response:
    """
    Make HTTP GET request with retry logic

    Args:
        url: URL to fetch
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        headers: Optional HTTP headers
        params: Optional query parameters

    Returns:
        Response object

    Raises:
        requests.RequestException: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            log_verbose(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
            response = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers, params=params)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise
            log_verbose(f"Request failed: {e}. Retrying...")
            time.sleep(2 ** attempt)  # Exponential backoff

    raise requests.RequestException("Max retries exceeded")


def detect_extension(url: str, content_type: Optional[str] = None) -> str:
    """
    Detect image file extension from URL or content type

    Args:
        url: Image URL
        content_type: Optional Content-Type header

    Returns:
        File extension (e.g., '.jpg', '.png')
    """
    # Try to get extension from URL
    parsed = urlparse(url)
    path = parsed.path
    if '.' in path:
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            return ext

    # Try to detect from content type
    if content_type:
        content_type = content_type.lower()
        if 'jpeg' in content_type or 'jpg' in content_type:
            return '.jpg'
        elif 'png' in content_type:
            return '.png'
        elif 'gif' in content_type:
            return '.gif'
        elif 'webp' in content_type:
            return '.webp'

    # Default to .jpg
    return '.jpg'


def download_and_save(url: str, target_path: str, headers: Optional[dict] = None):
    """
    Download image from URL and save to target path

    Args:
        url: Image URL
        target_path: Target file path
        headers: Optional HTTP headers
    """
    log_verbose(f"Downloading image from {url}")

    response = retry_request(url, headers=headers)

    # Auto-detect extension if needed
    target = Path(target_path)
    if not target.suffix or target.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        content_type = response.headers.get('Content-Type', '')
        ext = detect_extension(url, content_type)
        target = target.with_suffix(ext)
        log_verbose(f"Auto-detected extension: {ext}")

    # Create parent directory if needed
    target.parent.mkdir(parents=True, exist_ok=True)

    # Save image
    log_verbose(f"Saving image to {target}")
    with open(target, 'wb') as f:
        f.write(response.content)

    print(f"Successfully downloaded to: {target}")


def download_bing(target: str):
    """Download Bing Photo of the Day"""
    log_verbose("Fetching Bing Photo of the Day")

    url = "https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt=en-US"
    data = retry_request(url).json()

    if not data.get('images'):
        raise Exception("No images found in Bing response")

    urlbase = data['images'][0]['urlbase']
    img_url = f"https://www.bing.com{urlbase}_1920x1080.jpg"

    title = data['images'][0].get('title', 'Unknown')
    copyright_text = data['images'][0].get('copyright', 'Unknown')
    log_verbose(f"Photo: {title}")
    log_verbose(f"Copyright: {copyright_text}")

    download_and_save(img_url, target)


def download_nasa(target: str, api_key: str = "DEMO_KEY"):
    """Download NASA Astronomy Picture of the Day"""
    log_verbose("Fetching NASA APOD")

    url = f"https://api.nasa.gov/planetary/apod?api_key={api_key}"
    data = retry_request(url).json()

    # Check if it's an image (not a video)
    if data.get('media_type') != 'image':
        raise Exception(f"Today's APOD is not an image, it's a {data.get('media_type')}")

    # Prefer HD URL, fallback to regular URL
    img_url = data.get('hdurl') or data.get('url')
    if not img_url:
        raise Exception("No image URL found in NASA APOD response")

    title = data.get('title', 'Unknown')
    date = data.get('date', 'Unknown')
    log_verbose(f"Title: {title}")
    log_verbose(f"Date: {date}")

    download_and_save(img_url, target)


def download_wikipedia(target: str):
    """Download Wikipedia/Wikimedia Commons Picture of the Day"""
    log_verbose("Fetching Wikipedia Picture of the Day")

    from datetime import datetime

    # Get today's date
    now = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{now.year}/{now.month:02d}/{now.day:02d}"

    # Wikipedia requires a User-Agent header
    headers = {
        'User-Agent': 'any-photo-of-the-day/1.0 (https://github.com/yourusername/any-photo-of-the-day)'
    }

    response = retry_request(url, headers=headers)
    data = response.json()

    # Extract Picture of the Day
    potd = data.get('image')
    if not potd:
        raise Exception("No Picture of the Day found in Wikipedia response")

    # Get the full-resolution image URL
    img_url = potd.get('image', {}).get('source')
    if not img_url:
        raise Exception("No image URL found in Wikipedia Picture of the Day")

    # Get metadata
    title = potd.get('title', 'Unknown')
    description = potd.get('description', {}).get('text', 'No description')
    artist = potd.get('artist', {}).get('text', 'Unknown')

    log_verbose(f"Title: {title}")
    log_verbose(f"Artist: {artist}")
    log_verbose(f"Description: {description[:100]}..." if len(description) > 100 else f"Description: {description}")

    # Also need User-Agent header for downloading the image from Wikimedia
    download_and_save(img_url, target, headers=headers)


def download_unsplash(target: str, api_key: str, topic: Optional[str] = None, query: Optional[str] = None):
    """Download Unsplash photo (random or by topic) using official API"""
    log_verbose(f"Fetching Unsplash photo" + (f" (topic: {topic})" if topic else ""))

    if not api_key:
        raise Exception("Unsplash API key is required. Get one at https://unsplash.com/developers")

    # Use official Unsplash API
    url = "https://api.unsplash.com/photos/random"
    params = {'orientation': 'landscape'}

    if topic:
        params['topics'] = topic
        log_verbose(f"Using topic: {topic}")

    if query:
        params['query'] = query
        log_verbose(f"Using query: {query}")

    headers = {
        'Authorization': f'Client-ID {api_key}'
    }

    log_verbose(f"Fetching from Unsplash API: {url}")
    response = retry_request(url, headers=headers, params=params)

    # Parse JSON response
    data = response.json()

    # Get the full-size image URL
    img_url = data.get('urls', {}).get('full') or data.get('urls', {}).get('regular')
    if not img_url:
        raise Exception("No image URL found in Unsplash response")

    photographer = data.get('user', {}).get('name', 'Unknown')
    log_verbose(f"Photo by: {photographer}")

    download_and_save(img_url, target)


def main():
    """Main CLI entry point"""
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="Download photo of the day from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported sources:
  bing        Bing Photo of the Day
  nasa        NASA Astronomy Picture of the Day (APOD)
  wikipedia   Wikipedia/Wikimedia Commons Picture of the Day
  unsplash    Unsplash random photos

Examples:
  any_potd bing wallpaper.jpg
  any_potd nasa apod.jpg --api-key YOUR_NASA_KEY
  any_potd wikipedia wiki-potd.jpg --verbose
  any_potd unsplash nature.jpg --unsplash-api-key YOUR_KEY --topic nature
  any_potd unsplash mountain.jpg --unsplash-api-key YOUR_KEY --query "mountain sunset"
        """
    )

    parser.add_argument(
        'source',
        choices=['bing', 'nasa', 'wikipedia', 'unsplash'],
        help='Photo source'
    )

    parser.add_argument(
        'target',
        help='Target file path to save the image'
    )

    parser.add_argument(
        '--api-key',
        default='DEMO_KEY',
        help='NASA API key (default: DEMO_KEY with 30 req/hour limit)'
    )

    parser.add_argument(
        '--unsplash-api-key',
        help='Unsplash API key (required for unsplash source). Get one at https://unsplash.com/developers'
    )

    parser.add_argument(
        '--topic',
        help='Unsplash photo topic/category (e.g., nature, architecture, travel, food)'
    )

    parser.add_argument(
        '--query',
        help='Unsplash search query (e.g., "mountain sunset", "ocean waves")'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Set global verbose flag
    VERBOSE = args.verbose

    try:
        if args.source == 'bing':
            download_bing(args.target)
        elif args.source == 'nasa':
            download_nasa(args.target, args.api_key)
        elif args.source == 'wikipedia':
            download_wikipedia(args.target)
        elif args.source == 'unsplash':
            if not args.unsplash_api_key:
                print("Error: --unsplash-api-key is required for Unsplash source", file=sys.stderr)
                print("Get a free API key at: https://unsplash.com/developers", file=sys.stderr)
                sys.exit(1)
            download_unsplash(args.target, args.unsplash_api_key, args.topic, args.query)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
