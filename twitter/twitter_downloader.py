#!/usr/bin/env python3
"""
Twitter Media Downloader

A simple script to download videos and images from Twitter/X posts.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Optional
import argparse
import json

# Configure logging
logger = logging.getLogger(__name__)


class TwitterDownloader:
    """
    Twitter downloader class for downloading media from tweets.
    """
    
    def __init__(self, output_dir: str = "twitter_downloads"):
        """
        Initialize the Twitter downloader.
        
        Args:
            output_dir: Directory to save downloaded media files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
    def ensure_dependencies(self) -> bool:
        """
        Make sure required dependencies are installed.
        
        Returns:
            True if dependencies are installed, False otherwise
        """
        try:
            subprocess.check_call(
                ["yt-dlp", "--version"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info("✅ yt-dlp is already installed")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("yt-dlp not found, attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp"])
                logger.info("✅ yt-dlp installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install yt-dlp: {e}")
                return False
    
    def download_tweet(self, tweet_url: str, include_username: bool = True) -> Optional[List[str]]:
        """
        Download media from Twitter/X tweet.
        
        Args:
            tweet_url: Twitter/X tweet URL
            include_username: Whether to include username in filename
            
        Returns:
            List of downloaded file paths or None if download failed
        """
        try:
            # Determine output template
            if include_username:
                output_template = str(self.output_dir / "%(uploader)s_%(id)s.%(ext)s")
            else:
                output_template = str(self.output_dir / "%(id)s.%(ext)s")
            
            # Build command
            cmd = [
                "yt-dlp",
                "--output", output_template,
                "--write-info-json",
                "--no-check-certificate",
                tweet_url
            ]
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find downloaded files
            downloaded_files = []
            media_extensions = ['.mp4', '.jpg', '.jpeg', '.png', '.gif', '.webm', '.mkv', '.avi']
            
            for file in self.output_dir.iterdir():
                if file.is_file() and file.suffix.lower() in media_extensions:
                    downloaded_files.append(str(file))
            
            if downloaded_files:
                logger.info(f"✅ Downloaded {len(downloaded_files)} files from Twitter post")
                return downloaded_files
            else:
                logger.error("✅ Download completed but no media files found")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download Twitter post: {e}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading Twitter post: {e}")
            return None
    
    def download_multiple(self, tweet_urls: List[str], include_username: bool = True) -> Dict[str, List[str]]:
        """
        Download media from multiple Twitter posts.
        
        Args:
            tweet_urls: List of Twitter post URLs
            include_username: Whether to include username in filename
            
        Returns:
            Dictionary with "successful" and "failed" lists of URLs
        """
        results = {"successful": [], "failed": [], "output_files": []}
        
        for i, url in enumerate(tweet_urls, 1):
            logger.info(f"[{i}/{len(tweet_urls)}] Processing: {url}")
            
            output_files = self.download_tweet(url, include_username=include_username)
            
            if output_files:
                results["successful"].append(url)
                results["output_files"].extend(output_files)
            else:
                results["failed"].append(url)
        
        return results


def download_from_command_line():
    """Command-line interface for downloading Twitter media."""
    parser = argparse.ArgumentParser(description='Download media from Twitter/X posts')
    
    parser.add_argument('urls', nargs='*', help='Twitter/X post URLs to download')
    parser.add_argument('-i', '--input-file', help='File containing Twitter URLs (one per line)')
    parser.add_argument('-o', '--output-dir', default='twitter_downloads', help='Output directory')
    parser.add_argument('--no-username', action='store_true', help="Don't include username in filename")
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create downloader
    downloader = TwitterDownloader(output_dir=args.output_dir)
    
    # Install dependencies if requested
    if args.install_deps:
        if not downloader.ensure_dependencies():
            logger.error("Failed to install dependencies")
            return 1
        if len(args.urls) == 0 and not args.input_file:
            print("✅ Dependencies installed. Run again with Twitter URLs to download.")
            return 0
    
    # Get URLs from arguments or input file
    urls = []
    
    if args.urls:
        urls.extend(args.urls)
    
    if args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                file_urls = [line.strip() for line in f if line.strip()]
                urls.extend(file_urls)
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
    
    if not urls:
        parser.print_help()
        return 1
    
    # Download posts
    logger.info(f"Downloading {len(urls)} Twitter posts...")
    results = downloader.download_multiple(
        urls, 
        include_username=not args.no_username
    )
    
    # Print results
    print(f"\n📊 Download Results:")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    if results['failed']:
        print("\nFailed URLs:")
        for url in results['failed']:
            print(f"  - {url}")
    
    if results['output_files']:
        print(f"\n📁 Downloaded {len(results['output_files'])} files to {args.output_dir}/")
    
    return 0 if results['successful'] else 1


if __name__ == "__main__":
    sys.exit(download_from_command_line())
