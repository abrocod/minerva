# Evernote Notes Extractor for Mac

A Python script that extracts all notes from Evernote on macOS and saves them locally in an organized folder structure.

## Features

- ✅ Extracts all notes from all notebooks
- 📁 Organizes notes by notebook in separate folders
- 🏷️ Preserves note metadata (title, creation date, modification date, tags)
- 📝 Saves notes as HTML files with embedded styling
- 📊 Generates extraction metadata and logs
- 🔄 Progress tracking with detailed logging
- ⚡ Improved reliability with individual note extraction
- 🛡️ Error handling and recovery

## Requirements

- **macOS** (tested on macOS 10.14+)
- **Evernote app** installed and running
- **Python 3.6+**
- No additional Python packages required (uses only standard library)

## Installation

1. Clone or download this repository
2. Navigate to the `tools/evernote_extractor` directory
3. Make the script executable:
   ```bash
   chmod +x evernote_extractor_applescript.py
   ```

## Usage

### Basic Usage

1. **Start Evernote** on your Mac
2. Run the extractor:
   ```bash
   python3 evernote_extractor_applescript.py
   ```

### Command Line Options

```bash
# Extract to default directory (evernote_export)
python3 evernote_extractor_applescript.py

# Extract to custom directory
python3 evernote_extractor_applescript.py --output-dir /path/to/my/backup

# Check if Evernote is running and list notebooks
python3 evernote_extractor_applescript.py --check-only
```

### Output Structure

The script creates the following directory structure:

```
evernote_export/
├── notes/
│   ├── Notebook1/
│   │   ├── 0001_Note_Title.html
│   │   ├── 0002_Another_Note.html
│   │   └── ...
│   ├── Notebook2/
│   │   └── ...
│   └── ...
├── metadata/
│   └── extraction_metadata.json
└── logs/
    └── extraction_20231201_143022.log
```

### HTML Output Format

Each note is saved as an HTML file containing:
- **Metadata section**: Title, notebook, creation/modification dates, tags
- **Content section**: Original note content with formatting preserved
- **Styling**: Clean, readable CSS styling

## Permissions

When you first run the script, macOS may ask for permissions:

1. **Accessibility Access**: Allow Terminal/Python to control Evernote
2. **AppleScript Access**: Allow the script to communicate with Evernote

To grant permissions:
1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **Accessibility** and add Terminal (or your Python interpreter)
3. Select **Automation** and allow Terminal to control Evernote

## Troubleshooting

### Common Issues

**"Evernote is not running"**
- Solution: Start the Evernote app before running the script

**"AppleScript execution failed"**
- Check that Evernote is fully loaded (not just starting up)
- Ensure you have the latest version of Evernote
- Try restarting Evernote and running the script again

**Permission denied errors**
- Grant the necessary permissions in System Preferences (see Permissions section)
- Try running with `sudo` if file permission issues persist

**Timeout errors for large notes**
- The script includes timeout handling for large notes
- Failed extractions are logged and can be retried manually

**Special characters in note titles**
- The script automatically sanitizes filenames
- Original titles are preserved in the HTML content

### Performance Tips

- **Close other applications** to give Evernote more resources
- **For large libraries** (1000+ notes), consider running overnight
- **Monitor progress** through the detailed logging output
- **Check logs** if extraction seems to hang on specific notes

### Limitations

- **Attachments**: Currently extracts embedded content but may not preserve all attachment types
- **Formatting**: Complex formatting may not be perfectly preserved
- **Images**: Embedded images are included in HTML but may reference Evernote's internal storage
- **Encrypted notes**: Cannot extract password-protected notes

## Advanced Usage

### Resuming Failed Extractions

If extraction fails partway through:
1. Check the log file for the last successfully extracted note
2. The script will skip already extracted notes on restart
3. Failed notes are listed in the metadata JSON file

### Batch Processing

For very large libraries, you can process notebooks individually by modifying the script or using the metadata to identify problematic notebooks.

### Custom Output Formats

The script can be easily modified to output in different formats:
- Markdown files instead of HTML
- Plain text extraction
- JSON export of all metadata

## Script Versions

This repository includes two versions:

1. **`evernote_extractor.py`**: Basic version with batch processing
2. **`evernote_extractor_applescript.py`**: Improved version with individual note extraction (recommended)

Use the improved version (`evernote_extractor_applescript.py`) for better reliability and error handling.

## Contributing

Feel free to submit issues or pull requests to improve the script. Common enhancement areas:
- Better attachment handling
- Additional output formats
- GUI interface
- Incremental backup support

## License

This script is provided as-is for personal use. Please respect Evernote's terms of service when using this tool.

## Disclaimer

This tool is not affiliated with Evernote Corporation. Always maintain your original Evernote data as the primary source. Test the script with a small subset of notes before running on your entire library. 