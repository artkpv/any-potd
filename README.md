# any-photo-of-the-day

Download "photo of the day" from various sources via command line.

## Features

- **Multiple Sources**: Bing, NASA APOD, NASA EPIC, NASA Earth Observatory, Wikipedia, Met Museum, Unsplash, Flickr, Pexels
- **Simple CLI**: Easy-to-use command-line interface
- **Retry Logic**: Automatic retry on network failures
- **Verbose Mode**: Detailed logging with `--verbose` flag
- **Auto Format Detection**: Automatically detects and uses correct image format
- **Bash Script**: `set_potd.sh` — downloads and sets your Linux desktop wallpaper

## Installation

### From Source

```bash
git clone https://github.com/artkpv/any-potd.git
cd any-potd
uv venv
uv pip install -e .
```

## Usage

```bash
any_potd <source> <target> [options]
```

### Supported Sources

| Source | Description | Requirements |
|--------|-------------|--------------|
| `bing` | Bing Photo of the Day | None |
| `nasa` | NASA Astronomy Picture of the Day (APOD) | Optional API key |
| `earthobs` | NASA Earth Observatory Image of the Day | None |
| `epic` | NASA EPIC — full-disk Earth from 1 million miles (DSCOVR satellite) | None |
| `wikipedia` | Wikipedia/Wikimedia Commons Picture of the Day | None |
| `met` | Metropolitan Museum of Art — random public-domain highlight | None |
| `unsplash` | Unsplash random photos (with optional topic/query) | API key required |
| `flickr` | Flickr Explore interesting photos | API key required |
| `pexels` | Pexels curated photos | API key required |

### Examples

```bash
# No-key sources
python any_potd.py bing wallpaper.jpg
python any_potd.py earthobs earth.jpg --verbose
python any_potd.py epic epic.jpg --verbose
python any_potd.py wikipedia wiki.jpg --verbose
python any_potd.py met art.jpg --verbose

# NASA APOD (optional key, DEMO_KEY works for light use)
python any_potd.py nasa apod.jpg
python any_potd.py nasa apod.jpg --api-key YOUR_NASA_KEY

# Unsplash
python any_potd.py unsplash photo.jpg --unsplash-api-key YOUR_KEY
python any_potd.py unsplash nature.jpg --unsplash-api-key YOUR_KEY --topic nature
python any_potd.py unsplash mountain.jpg --unsplash-api-key YOUR_KEY --query "mountain sunset"

# Flickr
python any_potd.py flickr explore.jpg --flickr-api-key YOUR_KEY

# Pexels
python any_potd.py pexels curated.jpg --pexels-api-key YOUR_KEY
```

### Options

```
positional arguments:
  source                Photo source (see table above)
  target                Target file path

optional arguments:
  -h, --help            Show this help message and exit
  --api-key KEY         NASA API key (default: DEMO_KEY)
  --unsplash-api-key KEY  Unsplash API key
  --flickr-api-key KEY  Flickr API key
  --pexels-api-key KEY  Pexels API key
  --topic TOPIC         Unsplash topic/category
  --query QUERY         Unsplash search query
  --verbose, -v         Enable verbose output
```

### Environment Variables

API keys can be set via environment variables instead of flags:

| Variable | Source |
|----------|--------|
| `NASA_API_KEY` | `nasa` |
| `UNSPLASH_API_KEY` | `unsplash` |
| `FLICKR_API_KEY` | `flickr` |
| `PEXELS_API_KEY` | `pexels` |

## API Keys

| Source | Free Tier | Link |
|--------|-----------|------|
| NASA | `DEMO_KEY` built-in (30 req/hr); own key = 5,000 req/hr | https://api.nasa.gov/ |
| Unsplash | 50 req/hr demo, 5,000 req/hr production | https://unsplash.com/developers |
| Flickr | Free with account | https://www.flickr.com/services/api/ |
| Pexels | Free with account | https://www.pexels.com/api/ |

## Desktop Wallpaper (Linux)

`set_potd.sh` downloads an image, resizes it to 1920×1080, and sets it as wallpaper via `feh`:

```bash
./set_potd.sh bing
./set_potd.sh epic
./set_potd.sh met
./set_potd.sh pexels   # requires PEXELS_API_KEY env var
```

## Dependencies

- Python 3.8+
- `requests >= 2.31.0`

## License

MIT License

## Credits

- [Bing](https://www.bing.com) — daily photo
- [NASA APOD](https://apod.nasa.gov/) — Astronomy Picture of the Day
- [NASA Earth Observatory](https://earthobservatory.nasa.gov/) — satellite Earth imagery
- [NASA EPIC](https://epic.gsfc.nasa.gov/) — full-disk Earth photos from DSCOVR
- [Wikipedia](https://en.wikipedia.org/) / [Wikimedia Commons](https://commons.wikimedia.org/) — Picture of the Day
- [The Metropolitan Museum of Art](https://www.metmuseum.org/hubs/open-access) — open-access collection
- [Unsplash](https://unsplash.com) — curated stock photography
- [Flickr](https://www.flickr.com) — Explore interesting photos
- [Pexels](https://www.pexels.com) — curated stock photography
- Inspired by [photo-of-the-day](https://github.com/berkerol/photo-of-the-day) by berkerol

## Changelog

### v1.1.0
- Added `epic` source: NASA EPIC full-disk Earth imagery (no key needed)
- Added `met` source: Metropolitan Museum of Art random highlights (no key needed)
- Added `pexels` source: Pexels curated photos
- Added `earthobs` source: NASA Earth Observatory Image of the Day
- Added `flickr` source: Flickr Explore
- Fixed Earth Observatory RSS feed URL (migrated to science.nasa.gov)

### v1.0.0
- Initial release: Bing, NASA APOD, Wikipedia, Unsplash
