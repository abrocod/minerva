import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import yt_dlp
from openai import OpenAI
from prefect import flow, task
from prefect.logging import get_run_logger
from prefect.task_runners import SequentialTaskRunner
from dotenv import load_dotenv

from .downloader import DOWNLOAD_DIR, download_media

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set. Please set it to use transcription.")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

class TranscriptionError(Exception):
    """Custom exception for transcription errors"""
    pass

@task(retries=3, retry_delay_seconds=5)
def download_audio_task(url: str) -> str:
    """
    Downloads audio from YouTube URL using the existing downloader.
    
    Args:
        url: YouTube video URL
        
    Returns:
        Path to the downloaded audio file
        
    Raises:
        Exception: If download fails
    """
    logger = get_run_logger()
    logger.info(f"Starting audio download for URL: {url}")
    
    try:
        # Use a temporary directory for this specific download
        temp_dir = tempfile.mkdtemp(prefix="youtube_transcribe_")
        
        # Configure yt-dlp options for audio download
        ydl_opts = {
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,  # Reduce output for cleaner logs
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get the filename
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'unknown')
            
            # Download the audio
            ydl.download([url])
            
            # Find the downloaded file
            audio_files = list(Path(temp_dir).glob("*.mp3"))
            if not audio_files:
                raise Exception("No audio file found after download")
            
            audio_file_path = str(audio_files[0])
            logger.info(f"Audio downloaded successfully: {audio_file_path}")
            
            return audio_file_path
            
    except Exception as e:
        logger.error(f"Failed to download audio: {str(e)}")
        raise

@task(retries=3, retry_delay_seconds=10)
def transcribe_audio_task(audio_file_path: str, language: Optional[str] = None) -> Dict[str, Any]:
    """
    Transcribes audio file using OpenAI Whisper API.
    
    Args:
        audio_file_path: Path to the audio file
        language: Optional language code (e.g., 'en', 'es', 'fr')
        
    Returns:
        Dictionary containing transcription results
        
    Raises:
        TranscriptionError: If transcription fails
    """
    logger = get_run_logger()
    logger.info(f"Starting transcription for: {audio_file_path}")
    
    if not client:
        raise TranscriptionError("OpenAI API key not configured")
    
    try:
        # Check file size (Whisper API has a 25MB limit)
        file_size = os.path.getsize(audio_file_path)
        max_size = 25 * 1024 * 1024  # 25MB in bytes
        
        if file_size > max_size:
            logger.warning(f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds Whisper API limit (25MB)")
            raise TranscriptionError("Audio file too large for Whisper API (max 25MB)")
        
        # Prepare transcription parameters
        transcribe_params = {
            "model": "whisper-1",
            "response_format": "verbose_json",  # Get detailed response with timestamps
        }
        
        if language:
            transcribe_params["language"] = language
        
        # Transcribe the audio
        with open(audio_file_path, "rb") as audio_file:
            logger.info("Sending audio to OpenAI Whisper API...")
            response = client.audio.transcriptions.create(
                file=audio_file,
                **transcribe_params
            )
        
        logger.info("Transcription completed successfully")
        
        # Structure the response
        result = {
            "text": response.text,
            "language": getattr(response, 'language', language),
            "duration": getattr(response, 'duration', None),
            "segments": getattr(response, 'segments', []),
            "audio_file_path": audio_file_path
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Transcription failed: {str(e)}")
        raise TranscriptionError(f"Transcription failed: {str(e)}")

@task
def save_transcription_task(transcription_result: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Saves transcription results to a text file.
    
    Args:
        transcription_result: Dictionary containing transcription data
        output_path: Optional custom output path
        
    Returns:
        Path to the saved transcription file
    """
    logger = get_run_logger()
    
    if output_path is None:
        # Generate output filename based on audio file
        audio_path = Path(transcription_result["audio_file_path"])
        output_path = os.path.join(DOWNLOAD_DIR, f"{audio_path.stem}_transcript.txt")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("YouTube Video Transcription\n")
            f.write("=" * 50 + "\n\n")
            
            # Write basic info
            if transcription_result.get("language"):
                f.write(f"Language: {transcription_result['language']}\n")
            if transcription_result.get("duration"):
                f.write(f"Duration: {transcription_result['duration']:.2f} seconds\n")
            f.write(f"Audio file: {transcription_result['audio_file_path']}\n\n")
            
            # Write full transcript
            f.write("Full Transcript:\n")
            f.write("-" * 20 + "\n")
            f.write(transcription_result["text"])
            f.write("\n\n")
            
            # Write segments with timestamps if available
            if transcription_result.get("segments"):
                f.write("Timestamped Segments:\n")
                f.write("-" * 25 + "\n")
                for segment in transcription_result["segments"]:
                    start = segment.get("start", 0)
                    end = segment.get("end", 0)
                    text = segment.get("text", "")
                    f.write(f"[{start:.2f}s - {end:.2f}s]: {text.strip()}\n")
        
        logger.info(f"Transcription saved to: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Failed to save transcription: {str(e)}")
        raise

@task
def cleanup_temp_files_task(audio_file_path: str) -> None:
    """
    Cleans up temporary audio files.
    
    Args:
        audio_file_path: Path to the temporary audio file
    """
    logger = get_run_logger()
    
    try:
        # Remove the temporary directory and its contents
        temp_dir = os.path.dirname(audio_file_path)
        if temp_dir and "youtube_transcribe_" in temp_dir:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
    except Exception as e:
        logger.warning(f"Failed to cleanup temporary files: {str(e)}")

@flow(name="youtube-transcription", task_runner=SequentialTaskRunner())
def transcribe_youtube_video(
    url: str, 
    language: Optional[str] = None, 
    output_path: Optional[str] = None,
    keep_audio: bool = False
) -> Dict[str, str]:
    """
    Complete workflow to transcribe a YouTube video.
    
    Args:
        url: YouTube video URL
        language: Optional language code for transcription
        output_path: Optional custom output path for transcript
        keep_audio: Whether to keep the downloaded audio file
        
    Returns:
        Dictionary with paths to generated files
    """
    logger = get_run_logger()
    logger.info(f"Starting YouTube transcription workflow for: {url}")
    
    try:
        # Step 1: Download audio
        audio_file_path = download_audio_task(url)
        
        # Step 2: Transcribe audio
        transcription_result = transcribe_audio_task(audio_file_path, language)
        
        # Step 3: Save transcription
        transcript_path = save_transcription_task(transcription_result, output_path)
        
        # Step 4: Optionally keep or cleanup audio file
        final_audio_path = None
        if keep_audio:
            # Move audio file to downloads directory
            audio_filename = os.path.basename(audio_file_path)
            final_audio_path = os.path.join(DOWNLOAD_DIR, audio_filename)
            shutil.move(audio_file_path, final_audio_path)
            logger.info(f"Audio file saved to: {final_audio_path}")
            
            # Clean up the temp directory
            temp_dir = os.path.dirname(audio_file_path)
            if temp_dir and "youtube_transcribe_" in temp_dir:
                try:
                    os.rmdir(temp_dir)  # Remove empty temp directory
                except:
                    pass
        else:
            cleanup_temp_files_task(audio_file_path)
        
        result = {
            "transcript_path": transcript_path,
            "audio_path": final_audio_path,
            "transcription_text": transcription_result["text"]
        }
        
        logger.info("YouTube transcription workflow completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"Transcription workflow failed: {str(e)}")
        # Attempt cleanup on failure
        try:
            if 'audio_file_path' in locals():
                cleanup_temp_files_task(audio_file_path)
        except:
            pass
        raise

def main():
    """Command-line interface for the YouTube transcriber."""
    parser = argparse.ArgumentParser(
        description="Transcribe YouTube videos using OpenAI Whisper API and Prefect workflows."
    )
    parser.add_argument("url", help="YouTube video URL to transcribe")
    parser.add_argument(
        "--language", "-l", 
        help="Language code for transcription (e.g., 'en', 'es', 'fr')"
    )
    parser.add_argument(
        "--output", "-o", 
        help="Custom output path for transcript file"
    )
    parser.add_argument(
        "--keep-audio", "-k", 
        action="store_true",
        help="Keep the downloaded audio file"
    )
    
    args = parser.parse_args()
    
    # Validate OpenAI API key
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)
    
    try:
        # Run the transcription workflow
        result = transcribe_youtube_video(
            url=args.url,
            language=args.language,
            output_path=args.output,
            keep_audio=args.keep_audio
        )
        
        print("\n" + "="*50)
        print("TRANSCRIPTION COMPLETED SUCCESSFULLY!")
        print("="*50)
        print(f"Transcript saved to: {result['transcript_path']}")
        if result['audio_path']:
            print(f"Audio file saved to: {result['audio_path']}")
        print("\nFirst 200 characters of transcript:")
        print("-" * 40)
        print(result['transcription_text'][:200] + "..." if len(result['transcription_text']) > 200 else result['transcription_text'])
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 