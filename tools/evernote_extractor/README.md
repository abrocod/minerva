# Evernote Note Extractor

A Python tool to extract and parse notes from Evernote on macOS.

## Prerequisites

- macOS with Evernote app installed
- Python 3.6+
- Evernote must be running and logged in

## Features

- List all notebooks in your Evernote account
- Extract all notes from a specific notebook
- Export notes in multiple formats:
  - JSON (with both HTML and plain text content)
  - Markdown
  - HTML
- Automatic directory management using the Minerva directory structure
- Preserves note metadata (creation date, modification date, tags)

## Installation

No additional dependencies required - uses built-in Python libraries and macOS AppleScript.

## Usage

### Method 1: Manual Export and Parse (Recommended)

Due to Evernote's AppleScript limitations, the recommended approach is:

1. **Export from Evernote:**
   - Open Evernote on your Mac
   - Right-click on the notebook you want to export (e.g., "Eco")
   - Choose "Export Notebook..."
   - Select format: "Evernote XML Format (.enex)"
   - Save the file

2. **Parse the exported file:**

```bash
# Navigate to the extractor directory
cd minerva/tools/evernote_extractor

# Run the manual export guide
python manual_export_guide.py

# Or directly process an ENEX file
python manual_export_guide.py /path/to/export.enex json
python manual_export_guide.py /path/to/export.enex markdown
```

### Method 2: AppleScript Integration (Limited)

The AppleScript-based extractor has limited functionality due to Evernote's restricted AppleScript support:

```python
from minerva.tools.evernote_extractor import EvernoteExtractor

# Initialize extractor
extractor = EvernoteExtractor()

# Attempt to list notebooks (may not work with all Evernote versions)
extractor.list_all_notebooks()
```

## Output Location

By default, exported notes are saved to:
`/Users/jinchao/AlgoTrading/minerva_base/evernote_data/export/`

Files are named with the pattern: `{notebook_name}_{timestamp}.{format}`

## Export Formats

### JSON Format
- Contains structured data with all note metadata
- Includes both HTML and plain text versions of content
- Best for programmatic processing

### Markdown Format
- Human-readable format
- Preserves note structure and metadata
- Good for viewing in text editors or converting to other formats

### HTML Format
- Preserves original Evernote formatting
- Can be opened directly in browsers
- Includes styling for better readability

## Permissions

The first time you run this tool, macOS may ask for permission to control Evernote via AppleScript. You'll need to grant this permission in System Preferences > Security & Privacy > Privacy > Automation.

## Troubleshooting

1. **"Evernote not found" error**: Make sure Evernote is installed and running
2. **"Notebook not found" error**: Check the exact notebook name (case-sensitive)
3. **Empty export**: Ensure the notebook contains notes and Evernote is logged in
4. **Permission denied**: Grant AppleScript permissions in System Preferences

## Note

This tool uses AppleScript to communicate with Evernote, which means:
- Evernote must be running during extraction
- The extraction speed depends on the number of notes
- Large notebooks may take some time to export