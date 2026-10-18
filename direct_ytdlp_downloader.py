#!/usr/bin/env python3
"""
Direct yt-dlp Downloader

Uses direct yt-dlp commands for reliable YouTube downloads in 2025.
Based on best practices for handling YouTube's frequent changes.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


class DirectYTDLPDownloader:
    """Direct wrapper around yt-dlp for maximum reliability"""
    
    def __init__(self):
        """Initialize the downloader"""
        self.python_executable = sys.executable
    
    def ensure_ytdlp_installed(self):
        """Make sure yt-dlp is installed and up to date"""
        try:
            # Check if yt-dlp exists by importing it
            subprocess.run([self.python_executable, "-m", "yt_dlp", "--version"], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✅ yt-dlp is installed")
            
            # Update yt-dlp to latest version
            print("Updating yt-dlp to latest version...")
            subprocess.run([self.python_executable, "-m", "pip", "install", "-U", "yt-dlp[default]"], check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ yt-dlp not found, attempting to install...")
            
            try:
                # Attempt to install yt-dlp
                subprocess.run([self.python_executable, "-m", "pip", "install", "-U", "yt-dlp[default]"], check=True)
                print("✅ yt-dlp installed successfully")
                return True
            except subprocess.CalledProcessError:
                print("❌ Failed to install yt-dlp")
                print("\nPlease install yt-dlp manually:")
                print("python -m pip install -U \"yt-dlp[default]\"")
                return False
    
    def check_ffmpeg(self):
        """Check if ffmpeg is installed"""
        try:
            subprocess.run(["ffmpeg", "-version"], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("✅ ffmpeg is installed")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️ ffmpeg not found - some features may not work correctly")
            print("💡 Download ffmpeg from https://ffmpeg.org/download.html")
            return False
    
    def download_video(self, url, output_dir="downloads", format_type="video", 
                       include_title=True, create_playlist_structure=False,
                       quality="best", audio_format="m4a", video_format="mp4"):
        """
        Download a YouTube video using yt-dlp directly
        
        Args:
            url: YouTube URL to download
            output_dir: Directory to save downloads
            format_type: 'video', 'audio', or 'both'
            include_title: Include title in filename
            create_playlist_structure: Create uploader/playlist folder structure
            quality: Quality selection (best, worst, 720p, 1080p, etc.)
            audio_format: Audio format for audio downloads
            video_format: Video format for video downloads
        """
        # Create output directory
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Prepare output template
        if create_playlist_structure:
            output_template = os.path.join(output_dir, 
                                         "%(uploader)s/%(playlist)s/%(playlist_index)s - %(title).200B.%(ext)s")
        else:
            if include_title:
                output_template = os.path.join(output_dir, "%(id)s_%(title).200B.%(ext)s")
            else:
                output_template = os.path.join(output_dir, "%(id)s.%(ext)s")
        
        # Build command based on format type
        cmd = [self.python_executable, "-m", "yt_dlp"]
        
        if format_type == "audio":
            # Audio-only extraction
            cmd.extend(["-x", "--audio-format", audio_format])
            if quality != "best":
                cmd.extend(["--audio-quality", quality])
            cmd.extend(["-f", f"bestaudio[ext={audio_format}]/bestaudio"])
        elif format_type == "video":
            # Video download
            if quality == "best":
                cmd.extend(["-f", f"best[ext={video_format}]/best"])
            elif quality == "worst":
                cmd.extend(["-f", f"worst[ext={video_format}]/worst"])
            else:
                # Specific quality (e.g., 720p, 1080p)
                quality_num = quality.replace('p', '')
                cmd.extend(["-f", f"best[height<={quality_num}][ext={video_format}]/best[height<={quality_num}]"])
        elif format_type == "both":
            # Download both video and audio
            cmd.extend(["-f", "best", "--write-auto-sub", "--embed-subs"])
        
        # Add output template and URL
        cmd.extend(["-o", output_template, url])
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            subprocess.run(cmd, check=True)
            print(f"✅ Successfully downloaded from {url}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Download failed: {e}")
            return False


def main():
    """Main entry point for script"""
    parser = argparse.ArgumentParser(
        description="Download YouTube videos using direct yt-dlp commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Download video in MP4 format:
    python direct_ytdlp_downloader.py https://www.youtube.com/watch?v=L6yKk7EQYZc
    
  Download audio only:
    python direct_ytdlp_downloader.py -t audio https://www.youtube.com/watch?v=L6yKk7EQYZc
    
  Download MP3 audio:
    python direct_ytdlp_downloader.py -t audio -af mp3 https://www.youtube.com/watch?v=L6yKk7EQYZc
    
  Download 720p video:
    python direct_ytdlp_downloader.py -t video -q 720p https://www.youtube.com/watch?v=L6yKk7EQYZc
    
  Download playlist with folder structure:
    python direct_ytdlp_downloader.py -p https://www.youtube.com/playlist?list=PLXXX
        """
    )
    
    parser.add_argument("url", help="YouTube URL to download")
    parser.add_argument("-o", "--output-dir", default="custom_output", 
                       help="Output directory for downloads")
    parser.add_argument("-t", "--type", choices=["video", "audio", "both"], default="audio",
                       help="Download type (video, audio, or both)")
    parser.add_argument("-q", "--quality", default="best",
                       help="Quality (best, worst, 720p, 1080p, etc.)")
    parser.add_argument("-af", "--audio-format", default="m4a",
                       choices=["m4a", "mp3", "wav", "flac", "ogg"],
                       help="Audio format")
    parser.add_argument("-vf", "--video-format", default="mp4",
                       choices=["mp4", "webm", "mkv", "avi"],
                       help="Video format")
    parser.add_argument("-p", "--playlist", action="store_true",
                       help="Create uploader/playlist folder structure")
    parser.add_argument("-n", "--no-title", action="store_true",
                       help="Don't include video title in filename")
    parser.add_argument("-u", "--update", action="store_true",
                       help="Update yt-dlp before downloading")
    
    args = parser.parse_args()
    
    # Create downloader
    downloader = DirectYTDLPDownloader()
    
    # Update or install yt-dlp if needed
    if args.update or not downloader.ensure_ytdlp_installed():
        return 1
    
    # Check for ffmpeg
    downloader.check_ffmpeg()
    
    # Download the video
    success = downloader.download_video(
        args.url,
        output_dir=args.output_dir,
        format_type=args.type,
        include_title=not args.no_title,
        create_playlist_structure=args.playlist,
        quality=args.quality,
        audio_format=args.audio_format,
        video_format=args.video_format
    )
    
    if success:
        print(f"🎉 Download complete! Files saved to: {args.output_dir}")
        return 0
    else:
        print("❌ Download failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
