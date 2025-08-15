import argparse
import os
import sys

import yt_dlp

# Define the download directory relative to the script's location
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_DIR = os.path.join(SCRIPT_DIR, 'downloads')

def download_media(url: str, download_type: str) -> None:
    """
    Downloads media (video or audio) from the given URL using yt-dlp.

    Args:
        url: The URL of the YouTube video.
        download_type: 'video' or 'audio'.
    """
    # Ensure the download directory exists
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    common_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        'progress_hooks': [progress_hook],
        # Add other common options if needed, e.g., quiet: False
    }

    if download_type == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
        }
        print(f"Starting video download for: {url}")
    elif download_type == 'audio':
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192', # Standard quality MP3
            }],
        }
        print(f"Starting audio download (MP3) for: {url}")
        print("Note: Audio extraction requires ffmpeg to be installed.")
    else:
        print(f"Error: Invalid download type '{download_type}'. Choose 'video' or 'audio'.")
        sys.exit(1)

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"Download finished successfully!")
        print(f"File saved in: {DOWNLOAD_DIR}")
    except yt_dlp.utils.DownloadError as e:
        print(f"Error during download: {e}")
        # Consider more specific error handling if needed
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def progress_hook(d):
    """Displays download progress."""
    if d['status'] == 'downloading':
        # Display progress bar or percentage
        percent_str = d.get('_percent_str', 'N/A')
        speed_str = d.get('_speed_str', 'N/A')
        eta_str = d.get('_eta_str', 'N/A')
        total_bytes_str = d.get('_total_bytes_str', 'N/A') # or _total_bytes_estimate_str

        sys.stdout.write(f"Downloading: {percent_str} of {total_bytes_str} at {speed_str}, ETA: {eta_str}")
        sys.stdout.flush()
    elif d['status'] == 'finished':
        print(f"Download complete: {d['filename']}")
    elif d['status'] == 'error':
        print("Error during download hook.")


def main():
    parser = argparse.ArgumentParser(description="Download YouTube video or audio using yt-dlp.")
    parser.add_argument("url", help="The URL of the YouTube video to download.")
    args = parser.parse_args()

    while True:
        choice = input("Download video or audio? (v/a): ").lower().strip()
        if choice == 'v':
            download_type = 'video'
            break
        elif choice == 'a':
            download_type = 'audio'
            break
        else:
            print("Invalid choice. Please enter 'v' for video or 'a' for audio.")

    download_media(url=args.url, download_type=download_type)

if __name__ == "__main__":
    main()
