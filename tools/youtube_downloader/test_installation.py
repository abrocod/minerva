#!/usr/bin/env python3
"""
Test script to verify YouTube transcriber installation.

This script checks all dependencies and runs a basic functionality test.
"""

import os
import shutil
import sys
from pathlib import Path


def test_imports():
    """Test that all required packages can be imported."""
    print("🔍 Testing imports...")
    
    try:
        import yt_dlp
        print("✅ yt-dlp imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import yt-dlp: {e}")
        return False
    
    try:
        from openai import OpenAI
        print("✅ openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        return False
    
    try:
        import prefect
        print("✅ prefect imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import prefect: {e}")
        return False
    
    return True

def test_ffmpeg():
    """Test that FFmpeg is available."""
    print("\n🔍 Testing FFmpeg...")
    
    if shutil.which('ffmpeg'):
        print("✅ FFmpeg found in PATH")
        return True
    else:
        print("❌ FFmpeg not found in PATH")
        print("   Please install FFmpeg:")
        print("   - macOS: brew install ffmpeg")
        print("   - Ubuntu/Debian: sudo apt install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/")
        return False

def test_openai_key():
    """Test that OpenAI API key is configured."""
    print("\n🔍 Testing OpenAI API key...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        # Don't print the actual key for security
        print(f"✅ OpenAI API key found (length: {len(api_key)})")
        return True
    else:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("   Please set your API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False

def test_transcriber_import():
    """Test that the transcriber module can be imported."""
    print("\n🔍 Testing transcriber import...")
    
    try:
        # Add parent directories to path for import
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir.parent.parent))
        
        from tools.youtube_downloader.transcriber import (TranscriptionError,
                                                  transcribe_youtube_video)
        print("✅ Transcriber module imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import transcriber: {e}")
        return False
    except Exception as e:
        print(f"❌ Error importing transcriber: {e}")
        return False

def test_yt_dlp_functionality():
    """Test basic yt-dlp functionality."""
    print("\n🔍 Testing yt-dlp functionality...")
    
    try:
        import yt_dlp

        # Test with a simple info extraction (no download)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
        print(f"✅ yt-dlp working - extracted info for: {title[:50]}...")
        print(f"   Duration: {duration} seconds")
        return True
        
    except Exception as e:
        print(f"❌ yt-dlp test failed: {e}")
        return False

def test_openai_client():
    """Test OpenAI client initialization."""
    print("\n🔍 Testing OpenAI client...")
    
    try:
        from openai import OpenAI
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️  Skipping OpenAI client test (no API key)")
            return True
        
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized successfully")
        
        # Note: We don't test actual API calls to avoid charges
        print("   (API call test skipped to avoid charges)")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI client test failed: {e}")
        return False

def test_directories():
    """Test that required directories can be created."""
    print("\n🔍 Testing directory creation...")
    
    try:
        # Test creating downloads directory
        downloads_dir = Path(__file__).parent / "downloads"
        downloads_dir.mkdir(exist_ok=True)
        
        # Test creating a temp directory
        import tempfile
        temp_dir = tempfile.mkdtemp(prefix="test_transcriber_")
        
        # Clean up
        shutil.rmtree(temp_dir)
        
        print("✅ Directory creation test passed")
        return True
        
    except Exception as e:
        print(f"❌ Directory creation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 YouTube Transcriber Installation Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("FFmpeg Test", test_ffmpeg),
        ("OpenAI Key Test", test_openai_key),
        ("Transcriber Import Test", test_transcriber_import),
        ("yt-dlp Functionality Test", test_yt_dlp_functionality),
        ("OpenAI Client Test", test_openai_client),
        ("Directory Test", test_directories),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your installation is ready.")
        print("\nYou can now run:")
        print("  python transcriber.py 'https://www.youtube.com/watch?v=VIDEO_ID'")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Install missing packages: pip install -r requirements.txt")
        print("  - Install FFmpeg: brew install ffmpeg (macOS)")
        print("  - Set API key: export OPENAI_API_KEY='your-key'")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 