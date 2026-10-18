#!/usr/bin/env python3
"""
Website Content Downloader

A simple script to download content from websites including images, videos, and documents.
"""

import os
import sys
import subprocess
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
import argparse
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re

# Configure logging
logger = logging.getLogger(__name__)


class WebsiteDownloader:
    """
    Website downloader class for downloading various content from websites.
    """
    
    def __init__(self, output_dir: str = "website_downloads"):
        """
        Initialize the website downloader.
        
        Args:
            output_dir: Directory to save downloaded files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def ensure_dependencies(self) -> bool:
        """
        Make sure required dependencies are installed.
        
        Returns:
            True if dependencies are installed, False otherwise
        """
        try:
            import requests
            from bs4 import BeautifulSoup
            logger.info("✅ Required dependencies are available")
            return True
        except ImportError as e:
            logger.info(f"Missing dependencies: {e}")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "beautifulsoup4"])
                logger.info("✅ Dependencies installed successfully")
                return True
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install dependencies: {e}")
                return False
    
    def download_file(self, url: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Download a single file from URL.
        
        Args:
            url: URL to download
            filename: Optional custom filename
            
        Returns:
            Path to downloaded file or None if download failed
        """
        try:
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Determine filename
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename or '.' not in filename:
                    # Try to get filename from Content-Disposition header
                    content_disposition = response.headers.get('Content-Disposition', '')
                    if 'filename=' in content_disposition:
                        filename = content_disposition.split('filename=')[1].strip('"')
                    else:
                        # Generate a filename based on URL
                        filename = f"download_{hash(url) % 10000}"
                        # Try to guess extension from content-type
                        content_type = response.headers.get('Content-Type', '')
                        if 'image' in content_type:
                            if 'jpeg' in content_type or 'jpg' in content_type:
                                filename += '.jpg'
                            elif 'png' in content_type:
                                filename += '.png'
                            elif 'gif' in content_type:
                                filename += '.gif'
                        elif 'video' in content_type:
                            filename += '.mp4'
                        elif 'pdf' in content_type:
                            filename += '.pdf'
            
            # Sanitize filename
            filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
            
            output_path = self.output_dir / filename
            
            # Download file
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ Downloaded: {filename}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to download {url}: {e}")
            return None
    
    def download_images_from_page(self, page_url: str) -> List[str]:
        """
        Download all images from a webpage.
        
        Args:
            page_url: URL of the webpage
            
        Returns:
            List of downloaded file paths
        """
        downloaded_files = []
        
        try:
            response = self.session.get(page_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all image tags
            img_tags = soup.find_all('img')
            
            for img in img_tags:
                img_url = img.get('src') or img.get('data-src')
                if img_url:
                    # Convert relative URLs to absolute
                    img_url = urljoin(page_url, img_url)
                    
                    # Skip very small images (likely icons)
                    if any(skip in img_url.lower() for skip in ['icon', 'logo', 'avatar']) and '16x16' in img_url:
                        continue
                    
                    downloaded_file = self.download_file(img_url)
                    if downloaded_file:
                        downloaded_files.append(downloaded_file)
            
            logger.info(f"✅ Downloaded {len(downloaded_files)} images from {page_url}")
            
        except Exception as e:
            logger.error(f"❌ Failed to download images from {page_url}: {e}")
        
        return downloaded_files
    
    def download_videos_with_ytdlp(self, page_url: str) -> List[str]:
        """
        Try to download videos from a page using yt-dlp.
        
        Args:
            page_url: URL of the webpage
            
        Returns:
            List of downloaded file paths
        """
        try:
            # Check if yt-dlp is available
            subprocess.check_call(
                ["yt-dlp", "--version"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Try to download with yt-dlp
            cmd = [
                "yt-dlp",
                "--output", str(self.output_dir / "%(title)s.%(ext)s"),
                "--no-check-certificate",
                page_url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                # Find downloaded video files
                video_extensions = ['.mp4', '.webm', '.mkv', '.avi', '.mov']
                video_files = []
                
                for file in self.output_dir.iterdir():
                    if file.suffix.lower() in video_extensions:
                        video_files.append(str(file))
                
                logger.info(f"✅ Downloaded {len(video_files)} videos using yt-dlp")
                return video_files
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info("yt-dlp not available for video download")
        
        return []
    
    def download_from_url(self, url: str, download_images: bool = True, download_videos: bool = True) -> Dict[str, List[str]]:
        """
        Download content from a URL.
        
        Args:
            url: URL to download from
            download_images: Whether to download images
            download_videos: Whether to try downloading videos
            
        Returns:
            Dictionary with lists of downloaded files by type
        """
        results = {"images": [], "videos": [], "other": []}
        
        if download_images:
            results["images"] = self.download_images_from_page(url)
        
        if download_videos:
            results["videos"] = self.download_videos_with_ytdlp(url)
        
        return results


def download_from_command_line():
    """Command-line interface for downloading website content."""
    parser = argparse.ArgumentParser(description='Download content from websites')
    
    parser.add_argument('urls', nargs='*', help='Website URLs to download from')
    parser.add_argument('-i', '--input-file', help='File containing URLs (one per line)')
    parser.add_argument('-o', '--output-dir', default='website_downloads', help='Output directory')
    parser.add_argument('--no-images', action='store_true', help="Don't download images")
    parser.add_argument('--no-videos', action='store_true', help="Don't download videos")
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create downloader
    downloader = WebsiteDownloader(output_dir=args.output_dir)
    
    # Install dependencies if requested
    if args.install_deps:
        if not downloader.ensure_dependencies():
            logger.error("Failed to install dependencies")
            return 1
        if len(args.urls) == 0 and not args.input_file:
            print("✅ Dependencies installed. Run again with URLs to download.")
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
    
    # Download content
    total_files = 0
    
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Processing: {url}")
        
        results = downloader.download_from_url(
            url,
            download_images=not args.no_images,
            download_videos=not args.no_videos
        )
        
        url_total = len(results["images"]) + len(results["videos"]) + len(results["other"])
        total_files += url_total
        
        print(f"Downloaded from {url}: {len(results['images'])} images, {len(results['videos'])} videos")
    
    print(f"\n📁 Total files downloaded: {total_files} to {args.output_dir}/")
    
    return 0


if __name__ == "__main__":
    sys.exit(download_from_command_line())
