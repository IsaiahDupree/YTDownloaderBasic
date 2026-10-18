# Multi-Platform Media Downloader

A collection of modular downloaders for extracting media from various social media platforms and websites.

## Platforms Supported

- **YouTube** - Audio extraction from videos
- **Instagram** - Photos and videos from posts
- **TikTok** - Video downloads
- **Twitter/X** - Media from tweets
- **Websites** - Images, videos, and other content

## Project Structure

```text
├── youtube_downloader.py          # Main YouTube audio downloader
├── instagram/
│   └── instagram_downloader.py    # Instagram media downloader
├── tiktok/
│   └── tiktok_downloader.py       # TikTok video downloader
├── twitter/
│   └── twitter_downloader.py      # Twitter media downloader
├── websites/
│   └── website_downloader.py      # General website content downloader
├── requirements.txt               # All dependencies
└── README.md                      # This file
```

## Installation

1. Clone this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Or let each script install dependencies automatically with the `--install-deps` flag.

## Usage

### Enhanced YouTube Downloader

#### Main Downloader (youtube_downloader.py)

```bash
# Download audio (default)
python youtube_downloader.py https://www.youtube.com/watch?v=VIDEO_ID

# Download video
python youtube_downloader.py -t video https://www.youtube.com/watch?v=VIDEO_ID

# Download MP3 audio
python youtube_downloader.py -t audio -af mp3 https://www.youtube.com/watch?v=VIDEO_ID

# Download 720p video
python youtube_downloader.py -t video -q 720p https://www.youtube.com/watch?v=VIDEO_ID

# Download playlist
python youtube_downloader.py -p --playlist-folders https://www.youtube.com/playlist?list=PLAYLIST_ID

# Fix 403/400 errors with Android client
python youtube_downloader.py --android-client --cookies-from-browser chrome https://www.youtube.com/watch?v=VIDEO_ID

# Debug mode
set YTDLP_DEBUG=1
python youtube_downloader.py https://www.youtube.com/watch?v=VIDEO_ID
```

#### Direct yt-dlp Wrapper (direct_ytdlp_downloader.py)

```bash
# Simple video download
python direct_ytdlp_downloader.py https://www.youtube.com/watch?v=VIDEO_ID

# Audio-only MP3
python direct_ytdlp_downloader.py -t audio -af mp3 https://www.youtube.com/watch?v=VIDEO_ID

# Update yt-dlp and download
python direct_ytdlp_downloader.py -u https://www.youtube.com/watch?v=VIDEO_ID
```

### Instagram Downloader

```bash
python instagram/instagram_downloader.py https://www.instagram.com/p/POST_ID/
```

### TikTok Downloader

```bash
python tiktok/tiktok_downloader.py https://www.tiktok.com/@user/video/VIDEO_ID
```

### Twitter Downloader

```bash
python twitter/twitter_downloader.py https://twitter.com/user/status/TWEET_ID
```

### Website Content Downloader

```bash
python websites/website_downloader.py https://example.com
python websites/website_downloader.py --no-images https://example.com  # Videos only
```

## Common Options

All downloaders support:

- `-i, --input-file`: File containing URLs (one per line)
- `-o, --output-dir`: Custom output directory
- `--install-deps`: Install required dependencies

## Requirements

- Python 3.6+
- yt-dlp (for video/audio downloads)
- requests (for web scraping)
- beautifulsoup4 (for HTML parsing)

## Notes

- YouTube downloads may occasionally fail due to anti-bot measures
- Some platforms may require authentication for private content
- Always respect platform terms of service and copyright laws
