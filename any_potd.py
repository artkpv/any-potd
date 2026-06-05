#!/usr/bin/env python3
"""
any-photo-of-the-day: Download photo of the day from various sources

Supported sources:
- bing: Bing Photo of the Day
- nasa: NASA Astronomy Picture of the Day (APOD)
- earthobs: NASA Earth Observatory Image of the Day
- epic: NASA EPIC — full-disk Earth from 1M miles (DSCOVR satellite)
- wikipedia: Wikipedia/Wikimedia Commons Picture of the Day
- met: Metropolitan Museum of Art — random public-domain highlight
- unsplash: Unsplash random photos (with optional topics)
- flickr: Flickr Explore (interesting photos)
- pexels: Pexels curated photos
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

    # Request with thumbs=True so videos return a thumbnail image
    url = "https://api.nasa.gov/planetary/apod"
    params = {'api_key': api_key, 'thumbs': 'true'}
    data = retry_request(url, params=params).json()

    if data.get('media_type') == 'video':
        # Use thumbnail when today's APOD is a video
        img_url = data.get('thumbnail_url')
        if not img_url:
            raise Exception("Today's APOD is a video and no thumbnail is available")
        log_verbose("Today's APOD is a video — using thumbnail image")
    else:
        # Prefer HD URL, fallback to regular URL
        img_url = data.get('hdurl') or data.get('url')
        if not img_url:
            raise Exception("No image URL found in NASA APOD response")

    title = data.get('title', 'Unknown')
    date = data.get('date', 'Unknown')
    log_verbose(f"Title: {title}")
    log_verbose(f"Date: {date}")

    download_and_save(img_url, target)


def download_earth_observatory(target: str):
    """Download NASA Earth Observatory Image of the Day (satellite/earth imagery)"""
    import html
    import re
    import xml.etree.ElementTree as ET

    log_verbose("Fetching NASA Earth Observatory Image of the Day")

    url = "https://science.nasa.gov/feed/earth-observatory/image-of-the-day"
    headers = {'User-Agent': 'any-potd/1.0 (https://github.com/artkpv/any-potd)'}
    response = retry_request(url, headers=headers)

    root = ET.fromstring(response.text)
    ns = {
        'media': 'http://search.yahoo.com/mrss/',
        'content': 'http://purl.org/rss/1.0/modules/content/',
    }

    channel = root.find('channel')
    if channel is None:
        raise Exception("Invalid RSS feed from Earth Observatory")

    item = channel.find('item')
    if item is None:
        raise Exception("No items found in Earth Observatory RSS feed")

    title = item.findtext('title', 'Unknown')
    log_verbose(f"Title: {title}")

    img_url = None

    # Try media:content first, then enclosure, then content:encoded
    media_content = item.find('media:content', ns)
    if media_content is not None:
        img_url = media_content.get('url')
    else:
        enclosure = item.find('enclosure')
        if enclosure is not None:
            img_url = enclosure.get('url')
        else:
            content_encoded = item.find('content:encoded', ns)
            if content_encoded is not None and content_encoded.text:
                matches = re.findall(r'src="(https://[^"]+\.(?:jpg|jpeg|png))', content_encoded.text)
                if matches:
                    img_url = html.unescape(matches[0])

    if not img_url:
        raise Exception("No image URL found in Earth Observatory RSS")

    download_and_save(img_url, target, headers=headers)


def download_nasa_epic(target: str):
    """Download NASA EPIC full-disk Earth image (DSCOVR satellite, no key required)"""
    log_verbose("Fetching NASA EPIC Earth imagery")

    url = "https://epic.gsfc.nasa.gov/api/natural"
    headers = {'User-Agent': 'any-potd/1.0 (https://github.com/artkpv/any-potd)'}
    response = retry_request(url, headers=headers)

    images = response.json()
    if not images:
        raise Exception("No EPIC images available")

    img_data = images[0]
    image_name = img_data['image']
    date_str = img_data['date']  # "2026-06-05 00:31:45"
    year, month, day = date_str.split(' ')[0].split('-')

    img_url = f"https://epic.gsfc.nasa.gov/archive/natural/{year}/{month}/{day}/jpg/{image_name}.jpg"

    caption = img_data.get('caption', '')
    log_verbose(f"Date: {date_str}")
    if caption:
        log_verbose(f"Caption: {caption[:120]}")

    download_and_save(img_url, target, headers=headers)


def download_met_museum(target: str):
    """Download a random public-domain highlight from the Metropolitan Museum of Art"""
    import random

    log_verbose("Fetching Metropolitan Museum of Art highlight")

    headers = {'User-Agent': 'any-potd/1.0 (https://github.com/artkpv/any-potd)'}

    # Search highlighted artworks with images across a variety of categories
    terms = ['painting', 'sculpture', 'portrait', 'landscape', 'drawing',
             'textile', 'vessel', 'figure', 'still life', 'photograph']
    query = random.choice(terms)

    search_url = "https://collectionapi.metmuseum.org/public/collection/v1/search"
    params = {'isHighlight': 'true', 'hasImages': 'true', 'q': query}
    data = retry_request(search_url, headers=headers, params=params).json()

    object_ids = data.get('objectIDs') or []
    if not object_ids:
        raise Exception("No artworks found in Met Museum search")

    # Retry a few times in case a random pick has no primaryImage
    img_url = None
    for _ in range(5):
        object_id = random.choice(object_ids)
        obj_url = f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
        obj = retry_request(obj_url, headers=headers).json()
        img_url = obj.get('primaryImage')
        if img_url:
            title = obj.get('title', 'Unknown')
            artist = obj.get('artistDisplayName') or 'Unknown'
            date = obj.get('objectDate', '')
            log_verbose(f"Title: {title}")
            log_verbose(f"Artist: {artist}" + (f", {date}" if date else ""))
            break

    if not img_url:
        raise Exception("Could not find an artwork with an image in Met Museum collection")

    download_and_save(img_url, target, headers=headers)


def download_pexels(target: str, api_key: str):
    """Download the latest curated photo from Pexels"""
    log_verbose("Fetching Pexels curated photo")

    if not api_key:
        raise Exception("Pexels API key is required. Get one at https://www.pexels.com/api/")

    url = "https://api.pexels.com/v1/curated"
    headers = {'Authorization': api_key}
    params = {'per_page': 1}

    data = retry_request(url, headers=headers, params=params).json()

    photos = data.get('photos', [])
    if not photos:
        raise Exception("No photos found in Pexels curated feed")

    photo = photos[0]
    title = photo.get('alt', 'Unknown')
    photographer = photo.get('photographer', 'Unknown')
    log_verbose(f"Title: {title}")
    log_verbose(f"Photographer: {photographer}")

    src = photo.get('src', {})
    img_url = src.get('original') or src.get('large2x') or src.get('large')
    if not img_url:
        raise Exception("No image URL found in Pexels response")

    download_and_save(img_url, target, headers=headers)


def download_wikipedia(target: str):
    """Download Wikipedia/Wikimedia Commons Picture of the Day"""
    log_verbose("Fetching Wikipedia Picture of the Day")

    from datetime import datetime

    # Get today's date
    now = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{now.year}/{now.month:02d}/{now.day:02d}"

    # Wikipedia requires a User-Agent header
    headers = {
        'User-Agent': 'any-potd/1.0 (https://github.com/artkpv/any-potd)'
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


def download_flickr(target: str, api_key: str):
    """Download a photo from Flickr Explore (daily interesting photos)"""
    log_verbose("Fetching Flickr Explore photo")

    if not api_key:
        raise Exception("Flickr API key is required. Get one at https://www.flickr.com/services/api/")

    url = "https://api.flickr.com/services/rest/"
    params = {
        'method': 'flickr.interestingness.getList',
        'api_key': api_key,
        'format': 'json',
        'nojsoncallback': '1',
        'extras': 'url_o,url_h,url_l,title',
        'per_page': '1',
    }

    response = retry_request(url, params=params)
    data = response.json()

    if data.get('stat') != 'ok':
        raise Exception(f"Flickr API error: {data.get('message', 'Unknown error')}")

    photos = data.get('photos', {}).get('photo', [])
    if not photos:
        raise Exception("No photos found in Flickr Explore response")

    photo = photos[0]
    title = photo.get('title', 'Unknown')
    log_verbose(f"Title: {title}")

    # Try sizes in order of preference: original, huge (h), large (l)
    img_url = photo.get('url_o') or photo.get('url_h') or photo.get('url_l')
    if not img_url:
        # Construct URL from photo fields (size b = large 1024px)
        farm = photo.get('farm')
        server = photo.get('server')
        photo_id = photo.get('id')
        secret = photo.get('secret')
        img_url = f"https://farm{farm}.staticflickr.com/{server}/{photo_id}_{secret}_b.jpg"

    download_and_save(img_url, target)


def main():
    """Main CLI entry point"""
    global VERBOSE

    parser = argparse.ArgumentParser(
        description="Download photo of the day from various sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported sources:
  bing        Bing Photo of the Day (no key needed)
  nasa        NASA Astronomy Picture of the Day (optional API key)
  earthobs    NASA Earth Observatory Image of the Day (no key needed)
  epic        NASA EPIC full-disk Earth from 1M miles (no key needed)
  wikipedia   Wikipedia/Wikimedia Commons Picture of the Day (no key needed)
  met         Metropolitan Museum of Art random highlight (no key needed)
  unsplash    Unsplash random photos (API key required)
  flickr      Flickr Explore interesting photos (API key required)
  pexels      Pexels curated photos (API key required)

Examples:
  any_potd bing wallpaper.jpg
  any_potd nasa apod.jpg --api-key YOUR_NASA_KEY
  any_potd earthobs earth.jpg --verbose
  any_potd epic epic.jpg --verbose
  any_potd wikipedia wiki-potd.jpg --verbose
  any_potd met art.jpg --verbose
  any_potd unsplash nature.jpg --unsplash-api-key YOUR_KEY --topic nature
  any_potd unsplash mountain.jpg --unsplash-api-key YOUR_KEY --query "mountain sunset"
  any_potd flickr explore.jpg --flickr-api-key YOUR_KEY
  any_potd pexels curated.jpg --pexels-api-key YOUR_KEY
        """
    )

    parser.add_argument(
        'source',
        choices=['bing', 'nasa', 'earthobs', 'epic', 'wikipedia', 'met', 'unsplash', 'flickr', 'pexels'],
        help='Photo source'
    )

    parser.add_argument(
        'target',
        help='Target file path to save the image'
    )

    parser.add_argument(
        '--api-key',
        default=os.environ.get('NASA_API_KEY', 'DEMO_KEY'),
        help='NASA API key (default: NASA_API_KEY env var or DEMO_KEY with 30 req/hour limit)'
    )

    parser.add_argument(
        '--unsplash-api-key',
        default=os.environ.get('UNSPLASH_API_KEY'),
        help='Unsplash API key (required for unsplash source). Get one at https://unsplash.com/developers'
    )

    parser.add_argument(
        '--flickr-api-key',
        default=os.environ.get('FLICKR_API_KEY'),
        help='Flickr API key (required for flickr source). Get one at https://www.flickr.com/services/api/'
    )

    parser.add_argument(
        '--pexels-api-key',
        default=os.environ.get('PEXELS_API_KEY'),
        help='Pexels API key (required for pexels source). Get one at https://www.pexels.com/api/'
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
        elif args.source == 'earthobs':
            download_earth_observatory(args.target)
        elif args.source == 'epic':
            download_nasa_epic(args.target)
        elif args.source == 'wikipedia':
            download_wikipedia(args.target)
        elif args.source == 'met':
            download_met_museum(args.target)
        elif args.source == 'unsplash':
            if not args.unsplash_api_key:
                print("Error: --unsplash-api-key is required for Unsplash source", file=sys.stderr)
                print("Get a free API key at: https://unsplash.com/developers", file=sys.stderr)
                sys.exit(1)
            download_unsplash(args.target, args.unsplash_api_key, args.topic, args.query)
        elif args.source == 'flickr':
            if not args.flickr_api_key:
                print("Error: --flickr-api-key is required for Flickr source", file=sys.stderr)
                print("Get a free API key at: https://www.flickr.com/services/api/", file=sys.stderr)
                sys.exit(1)
            download_flickr(args.target, args.flickr_api_key)
        elif args.source == 'pexels':
            if not args.pexels_api_key:
                print("Error: --pexels-api-key is required for Pexels source", file=sys.stderr)
                print("Get a free API key at: https://www.pexels.com/api/", file=sys.stderr)
                sys.exit(1)
            download_pexels(args.target, args.pexels_api_key)
    except KeyboardInterrupt:
        print("\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
