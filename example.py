#!/usr/bin/env python3
"""
Example script showing how to use the YouTube Downloader
"""

from youtube_downloader import YouTubeDownloader

def main():
    # Create a downloader with default settings
    # This will download m4a files to the 'audio_samples' directory
    downloader = YouTubeDownloader()
    
    # Make sure dependencies are installed
    downloader.ensure_dependencies()
    
    # Example 1: Download a single video
    print("\nExample 1: Downloading a single video")
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    output_file = downloader.download_audio(url)
    if output_file:
        print(f"Successfully downloaded to: {output_file}")
    else:
        print("Download failed")
    
    # Example 2: Download multiple videos with title in filename
    print("\nExample 2: Downloading multiple videos with title in filename")
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
        "https://www.youtube.com/watch?v=jNQXAC9IVRw"   # Me at the zoo (first YouTube video)
    ]
    
    results = downloader.download_multiple(urls, include_title=True)
    
    print(f"Successfully downloaded: {len(results['successful'])}")
    print(f"Failed downloads: {len(results['failed'])}")
    
    if results['output_files']:
        print("\nDownloaded files:")
        for file in results['output_files']:
            print(f"- {file}")

if __name__ == "__main__":
    main()
