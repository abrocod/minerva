#!/usr/bin/env python3
"""
Simple YouTube video transcriber using OpenAI Whisper API.
No Prefect dependencies - just pure Python.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
import shutil

import yt_dlp
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '.env'))

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
DOWNLOAD_DIR = '/Users/jinchao/AlgoTrading/minerva_base/youtube_data/downloads'

def download_audio(url: str) -> str:
    """Download audio from YouTube URL."""
    print(f"Downloading audio from: {url}")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="youtube_transcribe_")
    
    # Configure yt-dlp options
    ydl_opts = {
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best[height<=480]/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'writesubtitles': False,
        'writeautomaticsub': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info and download
            info = ydl.extract_info(url, download=True)
            video_title = info.get('title', 'unknown')
            
        # Find the downloaded MP3 file
        mp3_files = list(Path(temp_dir).glob("*.mp3"))
        if not mp3_files:
            raise Exception("No MP3 file found after download")
        
        audio_path = str(mp3_files[0])
        print(f"Audio downloaded: {audio_path}")
        print(f"Video title: {video_title}")
        
        return audio_path, video_title
        
    except Exception as e:
        # Clean up on error
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Download failed: {str(e)}")

def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio using OpenAI Whisper API."""
    print("Starting transcription with OpenAI Whisper...")
    
    if not OPENAI_API_KEY:
        raise Exception("OPENAI_API_KEY not set in .env file")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Check file size (25MB limit)
    file_size = os.path.getsize(audio_path)
    max_size = 25 * 1024 * 1024
    
    if file_size > max_size:
        raise Exception(f"File too large ({file_size / 1024 / 1024:.1f}MB). Max is 25MB")
    
    try:
        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        # Convert segments to dict format if they exist
        segments = []
        if hasattr(response, 'segments') and response.segments:
            for segment in response.segments:
                segments.append({
                    'start': getattr(segment, 'start', 0),
                    'end': getattr(segment, 'end', 0),
                    'text': getattr(segment, 'text', '')
                })
        
        return {
            "text": response.text,
            "language": getattr(response, 'language', 'unknown'),
            "duration": getattr(response, 'duration', None),
            "segments": segments
        }
        
    except Exception as e:
        raise Exception(f"Transcription failed: {str(e)}")

def save_transcript(transcript: dict, video_title: str) -> str:
    """Save transcript to markdown file."""
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Create safe filename
    safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    output_path = os.path.join(DOWNLOAD_DIR, f"{safe_title}_transcript.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# YouTube Video Transcription\n\n")
        f.write(f"## Video Information\n\n")
        f.write(f"**Title:** {video_title}\n\n")
        f.write(f"**Language:** {transcript['language']}\n\n")
        
        if transcript['duration']:
            f.write(f"**Duration:** {transcript['duration']:.2f} seconds\n\n")
        
        f.write(f"## Full Transcript\n\n")
        f.write(transcript['text'])
        f.write("\n\n")
        
        # Add timestamped segments if available
        if transcript.get('segments'):
            f.write(f"## Timestamped Segments\n\n")
            
            for segment in transcript['segments']:
                start = segment.get('start', 0)
                end = segment.get('end', 0)
                text = segment.get('text', '').strip()
                f.write(f"**[{start:.2f}s - {end:.2f}s]:** {text}\n\n")
    
    return output_path

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Transcribe YouTube videos to text")
    parser.add_argument("url", help="YouTube video URL")
    parser.add_argument("--keep-audio", action="store_true", help="Keep the audio file")
    args = parser.parse_args()
    
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in .env file")
        print("Please check your .env file in:")
        print(f"  {os.path.join(script_dir, '.env')}")
        sys.exit(1)
    
    audio_path = None
    try:
        # Step 1: Download audio
        audio_path, video_title = download_audio(args.url)
        
        # Step 2: Transcribe
        transcript = transcribe_audio(audio_path)
        
        # Step 3: Save transcript
        output_path = save_transcript(transcript, video_title)
        
        # Step 4: Optionally keep audio
        if args.keep_audio:
            audio_filename = os.path.basename(audio_path)
            final_audio_path = os.path.join(DOWNLOAD_DIR, audio_filename)
            shutil.move(audio_path, final_audio_path)
            print(f"\nAudio saved to: {final_audio_path}")
        
        print("\n" + "=" * 50)
        print("TRANSCRIPTION COMPLETE!")
        print("=" * 50)
        print(f"Transcript saved to: {output_path}")
        print(f"\nFirst 500 characters:")
        print("-" * 40)
        preview = transcript['text'][:500] + "..." if len(transcript['text']) > 500 else transcript['text']
        print(preview)
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
        
    finally:
        # Clean up temp files
        if audio_path and os.path.exists(audio_path):
            temp_dir = os.path.dirname(audio_path)
            if "youtube_transcribe_" in temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    main()