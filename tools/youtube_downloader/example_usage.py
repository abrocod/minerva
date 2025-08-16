#!/usr/bin/env python3
"""
Example usage of the YouTube transcriber.

This script demonstrates how to use the transcriber both programmatically
and with different configuration options.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import the transcriber
sys.path.append(str(Path(__file__).parent.parent.parent))

from tools.youtube_downloader.transcriber import (TranscriptionError,
                                          transcribe_youtube_video)


def example_basic_transcription():
    """Example of basic transcription usage."""
    print("=== Basic Transcription Example ===")
    
    # Example YouTube URL (replace with actual URL)
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll for testing
    
    try:
        result = transcribe_youtube_video(url=url)
        
        print(f"✅ Transcription completed!")
        print(f"📄 Transcript saved to: {result['transcript_path']}")
        print(f"🎵 Audio file: {'Kept' if result['audio_path'] else 'Cleaned up'}")
        print(f"📝 First 100 characters: {result['transcription_text'][:100]}...")
        
    except TranscriptionError as e:
        print(f"❌ Transcription failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def example_advanced_transcription():
    """Example of advanced transcription with all options."""
    print("\n=== Advanced Transcription Example ===")
    
    # Example YouTube URL
    url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    # Custom output directory
    output_dir = Path("./transcripts")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / "my_transcript.txt"
    
    try:
        result = transcribe_youtube_video(
            url=url,
            language="en",  # Specify English
            output_path=str(output_path),
            keep_audio=True  # Keep the audio file
        )
        
        print(f"✅ Advanced transcription completed!")
        print(f"📄 Transcript saved to: {result['transcript_path']}")
        print(f"🎵 Audio saved to: {result['audio_path']}")
        print(f"📝 Transcript length: {len(result['transcription_text'])} characters")
        
        # Read and display part of the transcript
        with open(result['transcript_path'], 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"📖 Transcript preview:\n{content[:300]}...")
        
    except TranscriptionError as e:
        print(f"❌ Transcription failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def example_batch_transcription():
    """Example of transcribing multiple videos."""
    print("\n=== Batch Transcription Example ===")
    
    # List of YouTube URLs to transcribe
    urls = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=oHg5SJYRHA0",  # Another example
    ]
    
    results = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n🎬 Processing video {i}/{len(urls)}: {url}")
        
        try:
            result = transcribe_youtube_video(
                url=url,
                output_path=f"./transcripts/video_{i}_transcript.txt"
            )
            
            results.append({
                'url': url,
                'success': True,
                'transcript_path': result['transcript_path'],
                'text_length': len(result['transcription_text'])
            })
            
            print(f"✅ Video {i} completed: {result['transcript_path']}")
            
        except Exception as e:
            print(f"❌ Video {i} failed: {e}")
            results.append({
                'url': url,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print(f"\n📊 Batch Transcription Summary:")
    successful = sum(1 for r in results if r['success'])
    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {len(results) - successful}/{len(results)}")
    
    for i, result in enumerate(results, 1):
        if result['success']:
            print(f"  Video {i}: ✅ {result['text_length']} characters")
        else:
            print(f"  Video {i}: ❌ {result['error']}")

def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set it with: export OPENAI_API_KEY='your-api-key'")
        return False
    else:
        print("✅ OpenAI API key found")
    
    # Check dependencies
    try:
        import yt_dlp
        print("✅ yt-dlp installed")
    except ImportError:
        print("❌ yt-dlp not installed. Run: pip install yt-dlp")
        return False
    
    try:
        import openai
        print("✅ openai installed")
    except ImportError:
        print("❌ openai not installed. Run: pip install openai")
        return False
    
    try:
        import prefect
        print("✅ prefect installed")
    except ImportError:
        print("❌ prefect not installed. Run: pip install prefect")
        return False
    
    # Check FFmpeg
    import shutil
    if shutil.which('ffmpeg'):
        print("✅ FFmpeg found")
    else:
        print("❌ FFmpeg not found. Please install it:")
        print("   macOS: brew install ffmpeg")
        print("   Ubuntu: sudo apt install ffmpeg")
        return False
    
    print("✅ All prerequisites met!")
    return True

def main():
    """Main function to run examples."""
    print("🎥 YouTube Transcriber Examples")
    print("=" * 50)
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Please install missing dependencies.")
        return
    
    print("\n" + "=" * 50)
    
    # Run examples
    try:
        example_basic_transcription()
        example_advanced_transcription()
        example_batch_transcription()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Examples interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error in examples: {e}")
    
    print("\n🎉 Examples completed!")
    print("\nTo run the transcriber from command line:")
    print("python transcriber.py 'https://www.youtube.com/watch?v=VIDEO_ID'")

if __name__ == "__main__":
    main() 