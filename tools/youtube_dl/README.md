# YouTube Downloader and Transcriber

A comprehensive tool for downloading YouTube videos/audio and transcribing them using OpenAI's Whisper API with Prefect workflow management.

## Features

- **Download YouTube videos or audio** using `yt-dlp`
- **Automatic transcription** using OpenAI Whisper API
- **Workflow management** with Prefect for reliability and retry logic
- **Automatic retry** on failures with configurable delays
- **Timestamped transcripts** with detailed segment information
- **Multiple output formats** (text files with full transcript and timestamped segments)
- **Temporary file management** with automatic cleanup
- **Language detection** and custom language specification
- **File size validation** (Whisper API has 25MB limit)

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Install FFmpeg** (required for audio conversion):
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Set up OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

## Usage

### Command Line Interface

#### Basic transcription:
```bash
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

#### With language specification:
```bash
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --language en
```

#### Keep audio file after transcription:
```bash
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --keep-audio
```

#### Custom output path:
```bash
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" --output "/path/to/transcript.txt"
```

#### All options:
```bash
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID" \
    --language en \
    --output "/path/to/transcript.txt" \
    --keep-audio
```

### Python API

```python
from tools.youtube_dl import transcribe_youtube_video

# Basic usage
result = transcribe_youtube_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID"
)

# With options
result = transcribe_youtube_video(
    url="https://www.youtube.com/watch?v=VIDEO_ID",
    language="en",
    output_path="/path/to/transcript.txt",
    keep_audio=True
)

print(f"Transcript saved to: {result['transcript_path']}")
print(f"Audio saved to: {result['audio_path']}")
print(f"Transcript text: {result['transcription_text'][:200]}...")
```

### Prefect Workflow Management

The transcriber uses Prefect for workflow management, providing:

- **Automatic retries**: Download and transcription tasks retry 3 times on failure
- **Logging**: Comprehensive logging of all workflow steps
- **Error handling**: Graceful error handling with cleanup
- **Task isolation**: Each step is isolated for better debugging

#### View workflow in Prefect UI:
```bash
# Start Prefect server (optional)
prefect server start

# Run transcription (will appear in UI)
python transcriber.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Output Format

The transcriber generates a detailed text file with:

1. **Metadata**: Language, duration, source audio file
2. **Full transcript**: Complete transcription text
3. **Timestamped segments**: Individual segments with start/end times

Example output:
```
YouTube Video Transcription
==================================================

Language: en
Duration: 125.50 seconds
Audio file: /tmp/youtube_transcribe_xyz/video_title.mp3

Full Transcript:
--------------------
Welcome to this tutorial on machine learning. Today we'll be discussing...

Timestamped Segments:
-------------------------
[0.00s - 3.50s]: Welcome to this tutorial on machine learning.
[3.50s - 8.20s]: Today we'll be discussing the fundamentals of neural networks.
[8.20s - 12.80s]: Let's start with the basic concepts...
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)

### Supported Languages

The transcriber supports all languages supported by OpenAI Whisper:
- `en` - English
- `es` - Spanish  
- `fr` - French
- `de` - German
- `it` - Italian
- `pt` - Portuguese
- `ru` - Russian
- `ja` - Japanese
- `ko` - Korean
- `zh` - Chinese
- And many more...

## Error Handling

The transcriber includes comprehensive error handling:

- **Network failures**: Automatic retry with exponential backoff
- **API rate limits**: Retry with appropriate delays
- **File size limits**: Validation before API calls (25MB limit)
- **Invalid URLs**: Clear error messages
- **Missing dependencies**: Helpful installation instructions
- **Temporary file cleanup**: Automatic cleanup on success or failure

## Limitations

- **File size**: Audio files must be under 25MB (Whisper API limit)
- **Duration**: Very long videos may need to be split
- **API costs**: OpenAI Whisper API charges per minute of audio
- **Internet required**: Both for downloading and transcription

## Troubleshooting

### Common Issues

1. **"OPENAI_API_KEY not set"**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **"FFmpeg not found"**
   - Install FFmpeg using your system's package manager

3. **"File too large for Whisper API"**
   - The audio file exceeds 25MB limit
   - Try a shorter video or split the audio

4. **"Download failed"**
   - Check internet connection
   - Verify YouTube URL is valid and accessible
   - Some videos may be geo-restricted or private

### Debug Mode

For detailed logging, you can run with Python's logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run your transcription
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- [OpenAI Whisper](https://openai.com/research/whisper) for transcription
- [Prefect](https://www.prefect.io/) for workflow management 