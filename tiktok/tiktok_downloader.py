#!/usr/bin/env python3
"""
TikTok Video Downloader

A simple script to download videos from TikTok.
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


class TikTokDownloader:
    """
    TikTok downloader class for downloading videos.
    """
    
    def __init__(self, output_dir: str = "tiktok_downloads", video_format: str = "mp4"):
        """
        Initialize the TikTok downloader.
        
        Args:
            output_dir: Directory to save downloaded video files
            video_format: Format to save videos in
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.video_format = video_format
        
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
    
    def download_video(self, video_url: str, include_username: bool = True) -> Optional[str]:
        """
        Download video from TikTok.
        
        Args:
            video_url: TikTok video URL
            include_username: Whether to include username in filename
            
        Returns:
            Path to downloaded video file or None if download failed
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
                "--format", f"best[ext={self.video_format}]/best",
                "--output", output_template,
                "--write-info-json",
                "--no-check-certificate",
                video_url
            ]
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Find the output file
            video_files = list(self.output_dir.glob(f"*.{self.video_format}"))
            if not video_files:
                # Try other common video formats
                for ext in ['mp4', 'webm', 'mkv', 'avi']:
                    video_files = list(self.output_dir.glob(f"*.{ext}"))
                    if video_files:
                        break
            
            if video_files:
                # Get the most recently modified file
                output_file = max(video_files, key=lambda p: p.stat().st_mtime)
                logger.info(f"✅ Downloaded TikTok video: {output_file}")
                return str(output_file)
            else:
                logger.error("✅ Download completed but couldn't locate output file")
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download TikTok video: {e}")
            logger.error(f"Error output: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading TikTok video: {e}")
            return None
    
    def download_multiple(self, video_urls: List[str], include_username: bool = True) -> Dict[str, List[str]]:
        """
        Download multiple TikTok videos.
        
        Args:
            video_urls: List of TikTok video URLs
            include_username: Whether to include username in filename
            
        Returns:
            Dictionary with "successful" and "failed" lists of URLs
        """
        results = {"successful": [], "failed": [], "output_files": []}
        
        for i, url in enumerate(video_urls, 1):
            logger.info(f"[{i}/{len(video_urls)}] Processing: {url}")
            
            output_file = self.download_video(url, include_username=include_username)
            
            if output_file:
                results["successful"].append(url)
                results["output_files"].append(output_file)
            else:
                results["failed"].append(url)
        
        return results


def download_from_command_line():
    """Command-line interface for downloading TikTok videos."""
    parser = argparse.ArgumentParser(description='Download videos from TikTok')
    
    parser.add_argument('urls', nargs='*', help='TikTok video URLs to download')
    parser.add_argument('-i', '--input-file', help='File containing TikTok URLs (one per line)')
    parser.add_argument('-o', '--output-dir', default='tiktok_downloads', help='Output directory')
    parser.add_argument('-f', '--format', default='mp4', help='Video format')
    parser.add_argument('--no-username', action='store_true', help="Don't include username in filename")
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create downloader
    downloader = TikTokDownloader(
        output_dir=args.output_dir,
        video_format=args.format
    )
    
    # Install dependencies if requested
    if args.install_deps:
        if not downloader.ensure_dependencies():
            logger.error("Failed to install dependencies")
            return 1
        if len(args.urls) == 0 and not args.input_file:
            print("✅ Dependencies installed. Run again with TikTok URLs to download.")
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
    
    # Download videos
    logger.info(f"Downloading {len(urls)} TikTok videos...")
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
        print(f"\n📁 Downloaded {len(results['output_files'])} videos to {args.output_dir}/")
    
    return 0 if results['successful'] else 1


if __name__ == "__main__":
    sys.exit(download_from_command_line())
