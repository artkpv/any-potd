# any-photo-of-the-day

Download "photo of the day" from various sources via command line.

## Features

- **Multiple Sources**: Bing, NASA APOD, Wikipedia, Unsplash
- **Simple CLI**: Easy-to-use command-line interface
- **Retry Logic**: Automatic retry on network failures
- **Verbose Mode**: Detailed logging with `--verbose` flag
- **Auto Format Detection**: Automatically detects and uses correct image format

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/artkpv/any-potd.git
cd any-potd

# Create virtual environment and install
uv venv
uv pip install -e .
```

### Using pip (after publishing)

```bash
pip install any-photo-of-the-day
```

## Usage

### Basic Syntax

```bash
any_potd <source> <target> [options]
```

### Supported Sources

| Source | Description | Requirements |
|--------|-------------|--------------|
| `bing` | Bing Photo of the Day | None |
| `nasa` | NASA Astronomy Picture of the Day (APOD) | Optional API key |
| `wikipedia` | Wikipedia/Wikimedia Commons Picture of the Day | None |
| `unsplash` | Unsplash random photos with topics | API key required |

### Examples

#### Bing Photo of the Day

```bash
python any_potd.py bing wallpaper.jpg
python any_potd.py bing wallpaper.jpg --verbose
```

#### NASA APOD

```bash
# Using default DEMO_KEY (30 requests/hour limit)
python any_potd.py nasa apod.jpg

# Using your own API key
python any_potd.py nasa apod.jpg --api-key YOUR_NASA_API_KEY --verbose
```

**Get a NASA API key**: https://api.nasa.gov/

#### Wikipedia/Wikimedia Commons Picture of the Day

```bash
# Today's featured picture from Wikipedia/Wikimedia Commons
python any_potd.py wikipedia wiki-potd.jpg

# With verbose output showing title, artist, and description
python any_potd.py wikipedia wiki-potd.jpg --verbose
```

**Note**: Wikipedia provides very high-resolution images (often 5000+ pixels) with artist attribution and detailed descriptions.

#### Unsplash Random Photos

```bash
# Random photo with landscape orientation
python any_potd.py unsplash photo.jpg --unsplash-api-key YOUR_KEY

# Random photo from specific topic
python any_potd.py unsplash nature.jpg --unsplash-api-key YOUR_KEY --topic nature
python any_potd.py unsplash architecture.jpg --unsplash-api-key YOUR_KEY --topic architecture
python any_potd.py unsplash travel.jpg --unsplash-api-key YOUR_KEY --topic travel

# Search with query
python any_potd.py unsplash mountain.jpg --unsplash-api-key YOUR_KEY --query "mountain sunset"
```

**Get an Unsplash API key**: https://unsplash.com/developers

**Popular Unsplash Topics**: nature, architecture, travel, food, fashion, technology, animals, people, experimental

### Command-Line Options

```
positional arguments:
  source                Photo source: bing, nasa, unsplash
  target                Target file path to save the image

optional arguments:
  -h, --help            Show this help message and exit
  --api-key API_KEY     NASA API key (default: DEMO_KEY)
  --unsplash-api-key KEY
                        Unsplash API key (required for unsplash source)
  --topic TOPIC         Unsplash photo topic/category
  --query QUERY         Unsplash search query
  --verbose, -v         Enable verbose output
```

## API Keys

### NASA API Key

NASA provides a free `DEMO_KEY` with the following limits:
- 30 requests per hour
- 50 requests per day

For higher limits, get a free API key at https://api.nasa.gov/ (5,000 requests/hour).

### Unsplash API Key

Unsplash requires an API key for all requests:
1. Create a free account at https://unsplash.com/developers
2. Register a new application
3. Use your Application ID as the API key

**Limits**:
- Demo mode: 50 requests/hour
- Production mode: 5,000 requests/hour (requires application approval)

## Examples in Scripts

### Daily Wallpaper Script

```bash
#!/bin/bash
# Download Bing photo of the day as wallpaper
any_potd bing ~/Pictures/wallpaper.jpg && \
gsettings set org.gnome.desktop.background picture-uri "file:///$HOME/Pictures/wallpaper.jpg"
```

### Weekly NASA APOD Collection

```bash
#!/bin/bash
# Download NASA APOD to dated file
DATE=$(date +%Y-%m-%d)
any_potd nasa ~/Pictures/nasa-apod-$DATE.jpg --api-key YOUR_KEY --verbose
```

## Troubleshooting

### Network Errors

The tool automatically retries failed requests up to 3 times with exponential backoff. Use `--verbose` to see detailed error information.

### API Rate Limits

If you hit rate limits:
- **NASA**: Get your own API key or wait an hour
- **Unsplash**: Register your application or wait an hour

### Image Format

The tool automatically detects image format from the source. If the target filename has no extension or an incorrect one, it will be corrected automatically.

## Development

### Running Tests

```bash
# Test each source
python any_potd.py bing test_bing.jpg --verbose
python any_potd.py nasa test_nasa.jpg --verbose
python any_potd.py unsplash test_unsplash.jpg --unsplash-api-key YOUR_KEY --verbose
```

### Project Structure

```
any-photo-of-the-day/
├── any_potd.py          # Main script
├── pyproject.toml       # Package configuration
├── README.md            # Documentation
└── .gitignore           # Git ignore rules
```

## Dependencies

- Python 3.8+
- requests >= 2.31.0

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Credits

- [Bing](https://www.bing.com) for their daily photo service
- [NASA](https://apod.nasa.gov/) for the Astronomy Picture of the Day
- [Wikipedia](https://en.wikipedia.org/) and [Wikimedia Commons](https://commons.wikimedia.org/) for their Picture of the Day
- [Unsplash](https://unsplash.com) for their extensive photo library
- Inspired by [photo-of-the-day](https://github.com/berkerol/photo-of-the-day) by berkerol

## Changelog

### v1.0.0
- Initial release
- Support for Bing, NASA, Wikipedia, and Unsplash
- Automatic retry logic
- Verbose mode
- Auto format detection
