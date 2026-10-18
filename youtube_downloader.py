#!/usr/bin/env python3
"""
Modular YouTube Audio Downloader

A flexible, reusable library for downloading YouTube videos and extracting audio.
Can be used both as a command-line tool or imported into other projects.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Union, Optional
import argparse
import json
from urllib.parse import urlparse, parse_qs


# Configure logging
logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """
    Core YouTube downloader class that handles downloading videos and extracting audio.
    
    This class is designed to be used as a library and imported into other projects.
    """
    
    def __init__(self, 
                 output_dir: str = "downloads",
                 download_type: str = "audio",
                 audio_format: str = "m4a",
                 video_format: str = "mp4",
                 quality: str = "best",
                 use_yt_dlp: bool = True,
                 extra_args: Optional[List[str]] = None):
        """
        Initialize the YouTube downloader.
        
        Args:
            output_dir: Directory to save downloaded files
            download_type: Type of download ('audio', 'video', 'both')
            audio_format: Format to save audio in (m4a, mp3, wav, etc.)
            video_format: Format to save video in (mp4, webm, mkv, etc.)
            quality: Quality selection (best, worst, or specific like 720p)
            use_yt_dlp: Whether to use yt-dlp (True) or youtube-dl (False)
            extra_args: Additional arguments to pass to yt-dlp
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.download_type = download_type
        self.audio_format = audio_format
        self.video_format = video_format
        self.quality = quality
        self.downloader = "yt-dlp" if use_yt_dlp else "youtube-dl"
        self.extra_args = extra_args or []
        
    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL or video ID
            
        Returns:
            YouTube video ID
        """
        if "://" not in url and len(url) in (11, 12):  # likely a raw ID
            return url[:11]
        
        u = urlparse(url)
        if u.netloc.endswith("youtu.be"):
            return u.path.strip("/").split("/")[0]
        if "watch" in u.path:
            return parse_qs(u.query).get("v", [""])[0]
        if "/video/" in u.path:
            return u.path.split("/video/")[1].split("/")[0]
        if "studio.youtube.com/video/" in url:
            return url.split("studio.youtube.com/video/")[1].split("/")[0]
        
        # Fallback: assume it's already a video ID
        return url
    
    def ensure_dependencies(self) -> bool:
        """
        Make sure required dependencies are installed.
        
        Returns:
            True if dependencies are installed, False otherwise
        """
        # Check if yt-dlp is present
        try:
            subprocess.check_call(
                [self.downloader, "--version"], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            logger.info(f"✅ {self.downloader} is already installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.info(f"{self.downloader} not found, attempting to install...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", self.downloader])
                logger.info(f"✅ {self.downloader} installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Failed to install {self.downloader}: {e}")
                return False
        
        # Try to self-update yt-dlp (helps with YouTube churn)
        try:
            subprocess.check_call([self.downloader, "-U"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(f"✅ {self.downloader} updated successfully")
        except Exception:
            logger.info("yt-dlp self-update skipped/failed; continuing")
        
        # Check if ffmpeg is present
        try:
            subprocess.check_call(["ffmpeg", "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info("✅ ffmpeg is available")
        except Exception:
            logger.warning("ffmpeg not found; install it (e.g., choco install ffmpeg) for reliable audio extraction")
        
        return True
    
    def list_formats(self, video_url: str) -> bool:
        """
        List all available formats for a YouTube video.
        
        Args:
            video_url: YouTube URL or video ID
            
        Returns:
            True if successful, False otherwise
        """
        video_id = self.extract_video_id(video_url)
        
        try:
            cmd = [
                self.downloader,
                "-F",  # List formats
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            
            # Add extra arguments if available
            if self.extra_args:
                cmd[1:1] = self.extra_args
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"\n📋 Available formats for {video_id}:")
                print(result.stdout)
                return True
            else:
                logger.error(f"Failed to list formats: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error listing formats: {e}")
            return False
    
    def download_media(self, video_url: str, 
                      output_path: Optional[str] = None,
                      include_video_id: bool = True,
                      include_title: bool = False,
                      download_type: Optional[str] = None,
                      custom_format: Optional[str] = None) -> Optional[str]:
        """
        Download media from YouTube video.
        
        Args:
            video_url: YouTube URL or video ID
            output_path: Optional custom output path
            include_video_id: Whether to include video ID in filename
            include_title: Whether to include video title in filename
            download_type: Override default download type ('audio', 'video', 'both')
            custom_format: Custom format selector (e.g., 'best[height<=720]', 'mp4')
            
        Returns:
            Path to downloaded file or None if download failed
        """
        video_id = self.extract_video_id(video_url)
        current_download_type = download_type or self.download_type
        
        # Determine output template
        if output_path:
            output_template = output_path
        else:
            if include_title and include_video_id:
                output_template = str(self.output_dir / "%(id)s_%(title).200B.%(ext)s")
            elif include_title:
                output_template = str(self.output_dir / "%(title).200B.%(ext)s")
            elif include_video_id:
                output_template = str(self.output_dir / "%(id)s.%(ext)s") 
            else:
                # Use just the numeric hash of the video ID to anonymize
                import hashlib
                filename = hashlib.md5(video_id.encode()).hexdigest()[:10]
                output_template = str(self.output_dir / f"{filename}.%(ext)s")
        
        try:
            # Build command based on download type
            cmd = [self.downloader]
            
            if custom_format:
                # Use custom format selector
                cmd.extend(["-f", custom_format])
                if current_download_type == "audio":
                    cmd.extend(["-x", "--audio-format", self.audio_format])
            elif current_download_type == "audio":
                cmd.extend(["-x", "--audio-format", self.audio_format])
                if self.quality != "best":
                    cmd.extend(["--audio-quality", self.quality])
                cmd.extend(["-f", f"bestaudio[ext={self.audio_format}]/bestaudio"])
            elif current_download_type == "video":
                if self.quality == "best":
                    cmd.extend(["-f", f"best[ext={self.video_format}]/best"])
                elif self.quality == "worst":
                    cmd.extend(["-f", f"worst[ext={self.video_format}]/worst"])
                else:
                    # Handle specific quality (e.g., 720p, 1080p)
                    quality_num = self.quality.replace('p', '') if 'p' in self.quality else self.quality
                    cmd.extend(["-f", f"best[height<={quality_num}][ext={self.video_format}]/best[height<={quality_num}]"])
            elif current_download_type == "both":
                cmd.extend(["-f", "best", "--write-auto-sub", "--embed-subs"])
            elif current_download_type == "all":
                # Download all available formats
                cmd.extend(["-f", "all"])
            
            cmd.extend(["--output", output_template, f"https://www.youtube.com/watch?v={video_id}"])
            
            # Add extra arguments (cookies, player client, etc.)
            if self.extra_args:
                cmd[1:1] = self.extra_args  # inject extras right after the binary
            
            # Add debug mode if environment variable is set
            if os.getenv("YTDLP_DEBUG") == "1":
                cmd.insert(1, "-v")
            
            # Take snapshot of files before download for include_title option
            if include_title:
                file_pattern = f"*{video_id}*.*"
                before_files = set(self.output_dir.glob(file_pattern))
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"yt-dlp failed:\n{result.stderr}")
                return None
            
            # Find the output file
            if include_title:
                file_pattern = f"*{video_id}*.*"
                after_files = set(self.output_dir.glob(file_pattern))
                new_files = after_files - before_files
                output_file = next(iter(new_files), None)
                if not output_file:
                    # Try to find by just looking at recent files
                    files = list(self.output_dir.glob("*.*"))
                    output_file = max(files, key=lambda p: p.stat().st_mtime) if files else None
            else:
                # We can predict the filename based on download type
                if include_video_id:
                    if current_download_type == "audio":
                        output_file = self.output_dir / f"{video_id}.{self.audio_format}"
                    else:
                        output_file = self.output_dir / f"{video_id}.{self.video_format}"
                else:
                    # Use hash
                    import hashlib
                    filename = hashlib.md5(video_id.encode()).hexdigest()[:10]
                    ext = self.audio_format if current_download_type == "audio" else self.video_format
                    output_file = self.output_dir / f"{filename}.{ext}"
            
            if output_file and output_file.exists():
                logger.info(f"✅ Downloaded {current_download_type}: {output_file}")
                return str(output_file)
            else:
                logger.error(f"✅ Download completed but couldn't locate output file")
                # Return any file that looks like it might be the right one
                potential_files = list(self.output_dir.glob("*.*"))
                if potential_files:
                    newest_file = max(potential_files, key=lambda p: p.stat().st_mtime)
                    logger.info(f"Using most recently modified file: {newest_file}")
                    return str(newest_file)
                return None
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to download {video_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading {video_id}: {e}")
            return None
    
    def download_audio(self, video_url: str, **kwargs) -> Optional[str]:
        """Legacy method for audio downloads"""
        return self.download_media(video_url, download_type="audio", **kwargs)
    
    def download_video(self, video_url: str, **kwargs) -> Optional[str]:
        """Download video from YouTube"""
        return self.download_media(video_url, download_type="video", **kwargs)
    
    def download_playlist(self, playlist_url: str, 
                         max_downloads: Optional[int] = None,
                         create_folder_structure: bool = True) -> Dict[str, List[str]]:
        """
        Download entire playlist from YouTube.
        
        Args:
            playlist_url: YouTube playlist URL
            max_downloads: Maximum number of videos to download
            create_folder_structure: Create uploader/playlist folder structure
            
        Returns:
            Dictionary with "successful" and "failed" lists of URLs
        """
        try:
            # Build command for playlist
            cmd = [self.downloader]
            
            if self.download_type == "audio":
                cmd.extend(["-x", "--audio-format", self.audio_format])
                cmd.extend(["-f", f"bestaudio[ext={self.audio_format}]/bestaudio"])
            elif self.download_type == "video":
                cmd.extend(["-f", f"best[ext={self.video_format}]/best"])
            
            # Output template for playlist
            if create_folder_structure:
                output_template = str(self.output_dir / "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title).200B.%(ext)s")
            else:
                output_template = str(self.output_dir / "%(playlist_index)s - %(title).200B.%(ext)s")
            
            cmd.extend(["--output", output_template])
            
            if max_downloads:
                cmd.extend(["--playlist-end", str(max_downloads)])
            
            # Add extra arguments
            if self.extra_args:
                cmd[1:1] = self.extra_args
            
            cmd.append(playlist_url)
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ Downloaded playlist successfully")
                # Count downloaded files
                downloaded_files = list(self.output_dir.rglob("*.*"))
                return {"successful": [playlist_url], "failed": [], "output_files": [str(f) for f in downloaded_files]}
            else:
                logger.error(f"yt-dlp failed:\n{result.stderr}")
                return {"successful": [], "failed": [playlist_url], "output_files": []}
                
        except Exception as e:
            logger.error(f"❌ Unexpected error downloading playlist: {e}")
            return {"successful": [], "failed": [playlist_url], "output_files": []}
    
    def download_multiple(self, video_urls: List[str], 
                         include_video_id: bool = True,
                         include_title: bool = False,
                         download_type: Optional[str] = None,
                         custom_format: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Download media from multiple YouTube videos.
        
        Args:
            video_urls: List of YouTube URLs or video IDs
            include_video_id: Whether to include video ID in filename
            include_title: Whether to include video title in filename
            download_type: Override default download type
            custom_format: Custom format selector
            
        Returns:
            Dictionary with "successful" and "failed" lists of URLs
        """
        results = {"successful": [], "failed": [], "output_files": []}
        
        for i, url in enumerate(video_urls, 1):
            logger.info(f"[{i}/{len(video_urls)}] Processing: {url}")
            
            output_file = self.download_media(
                url, 
                include_video_id=include_video_id,
                include_title=include_title,
                download_type=download_type,
                custom_format=custom_format
            )
            
            if output_file:
                results["successful"].append(url)
                results["output_files"].append(output_file)
            else:
                results["failed"].append(url)
        
        return results
    
    def get_downloaded_files(self) -> List[str]:
        """
        Get list of downloaded audio files.
        
        Returns:
            List of paths to downloaded audio files
        """
        audio_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.webm', '.mp4', '.flac']
        files = []
        
        for file in self.output_dir.iterdir():
            if file.suffix.lower() in audio_extensions:
                files.append(str(file))
        
        return files


def download_from_command_line():
    """Command-line interface for downloading YouTube videos."""
    parser = argparse.ArgumentParser(
        description='Enhanced YouTube downloader with video/audio support',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Download audio (default):
    python youtube_downloader.py https://www.youtube.com/watch?v=VIDEO_ID
    
  Download video:
    python youtube_downloader.py -t video https://www.youtube.com/watch?v=VIDEO_ID
    
  Download MP3 audio:
    python youtube_downloader.py -t audio -af mp3 https://www.youtube.com/watch?v=VIDEO_ID
    
  Download 720p video:
    python youtube_downloader.py -t video -q 720p https://www.youtube.com/watch?v=VIDEO_ID
    
  Download playlist:
    python youtube_downloader.py -p https://www.youtube.com/playlist?list=PLAYLIST_ID
    
  Fix 403 errors with Android client:
    python youtube_downloader.py --android-client --cookies-from-browser chrome URL
        """
    )
    
    parser.add_argument('urls', nargs='*', help='YouTube URLs to download')
    parser.add_argument('-i', '--input-file', help='File containing YouTube URLs (one per line)')
    parser.add_argument('-o', '--output-dir', default='downloads', help='Output directory')
    
    # Download type options
    parser.add_argument('-t', '--type', choices=['audio', 'video', 'both', 'all'], default='audio',
                       help='Download type (default: audio)')
    parser.add_argument('-af', '--audio-format', default='m4a', 
                       choices=['m4a', 'mp3', 'wav', 'flac', 'ogg'],
                       help='Audio format (default: m4a)')
    parser.add_argument('-vf', '--video-format', default='mp4',
                       choices=['mp4', 'webm', 'mkv', 'avi'],
                       help='Video format (default: mp4)')
    parser.add_argument('-q', '--quality', default='best',
                       help='Quality (best, worst, 720p, 1080p, etc.)')
    
    # Filename options
    parser.add_argument('--no-video-id', action='store_true', help="Don't include video ID in filename")
    parser.add_argument('--include-title', action='store_true', help="Include video title in filename")
    
    # Playlist options
    parser.add_argument('-p', '--playlist', action='store_true', help='Download as playlist')
    parser.add_argument('--max-downloads', type=int, help='Maximum number of videos to download from playlist')
    parser.add_argument('--playlist-folders', action='store_true', help='Create uploader/playlist folder structure')
    
    # Format options
    parser.add_argument('-F', '--list-formats', action='store_true', help='List all available formats and exit')
    parser.add_argument('--format', help='Custom format selector (e.g., "best[height<=720]", "mp4", "137+140")')
    
    # Advanced options
    parser.add_argument('--install-deps', action='store_true', help='Install required dependencies')
    parser.add_argument('--cookies-from-browser', choices=['chrome','firefox','edge'], help='Import cookies from this browser')
    parser.add_argument('--cookies', help='Path to cookies.txt file')
    parser.add_argument('--android-client', action='store_true', help='Use YouTube Android player client')
    parser.add_argument('--force-ipv4', action='store_true', help='Force IPv4 connections')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Build extra arguments from CLI options
    extra_args = []
    if args.cookies_from_browser:
        extra_args += ['--cookies-from-browser', args.cookies_from_browser]
    if args.cookies:
        extra_args += ['--cookies', args.cookies]
    if args.android_client:
        extra_args += ['--extractor-args', 'youtube:player-client=android']
    if args.force_ipv4:
        extra_args += ['--force-ipv4']
    
    # Create downloader
    downloader = YouTubeDownloader(
        output_dir=args.output_dir,
        download_type=args.type,
        audio_format=args.audio_format,
        video_format=args.video_format,
        quality=args.quality,
        extra_args=extra_args
    )
    
    # Install dependencies if requested
    if args.install_deps:
        if not downloader.ensure_dependencies():
            logger.error("Failed to install dependencies")
            return 1
        if len(args.urls) == 0 and not args.input_file:
            print("✅ Dependencies installed. Run again with YouTube URLs to download.")
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
    
    # Handle format listing
    if args.list_formats:
        for url in urls:
            downloader.list_formats(url)
        return 0
    
    # Handle playlist vs individual videos
    if args.playlist:
        if len(urls) != 1:
            logger.error("Playlist mode requires exactly one playlist URL")
            return 1
        
        logger.info(f"Downloading playlist: {urls[0]}")
        results = downloader.download_playlist(
            urls[0],
            max_downloads=args.max_downloads,
            create_folder_structure=args.playlist_folders
        )
    else:
        # Download individual videos
        logger.info(f"Downloading {len(urls)} videos...")
        results = downloader.download_multiple(
            urls, 
            include_video_id=not args.no_video_id,
            include_title=args.include_title,
            custom_format=args.format
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
        file_type = args.type if not args.playlist else "playlist items"
        print(f"\n📁 Downloaded {len(results['output_files'])} {file_type} files to {args.output_dir}/")
    
    return 0 if results['successful'] else 1


if __name__ == "__main__":
    sys.exit(download_from_command_line())
