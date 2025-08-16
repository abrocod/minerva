#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from minerva.tools.evernote_extractor.enex_parser import ENEXParser
from minerva.directory_manager.directory_definition import EvernoteDirectory
from pathlib import Path
import json


def process_enex_file(enex_file_path: str, output_format: str = 'json'):
    """Process an ENEX file exported from Evernote"""
    
    parser = ENEXParser()
    evernote_dir = EvernoteDirectory()
    output_dir = Path(evernote_dir.get_export_dir())
    
    print(f"Processing ENEX file: {enex_file_path}")
    
    # Parse the ENEX file
    notes = parser.parse_enex_file(enex_file_path)
    print(f"Found {len(notes)} notes")
    
    # Generate output filename
    input_filename = Path(enex_file_path).stem
    
    if output_format == 'json':
        output_file = output_dir / f"{input_filename}_parsed.json"
        parser.export_to_json(notes, str(output_file))
    elif output_format == 'markdown':
        output_file = output_dir / f"{input_filename}_parsed.md"
        parser.export_to_markdown(notes, str(output_file))
    else:
        print(f"Unsupported format: {output_format}")
        return None
    
    print(f"✅ Successfully exported to: {output_file}")
    return str(output_file)


def main():
    print("=" * 60)
    print("Evernote Manual Export Guide")
    print("=" * 60)
    print()
    print("Since direct AppleScript access to Evernote is limited,")
    print("please follow these steps to export your notes:")
    print()
    print("STEP 1: Export from Evernote")
    print("-" * 30)
    print("1. Open Evernote on your Mac")
    print("2. Select the notebook you want to export (e.g., 'Eco')")
    print("3. Right-click on the notebook")
    print("4. Choose 'Export Notebook...'")
    print("5. Select format: 'Evernote XML Format (.enex)'")
    print("6. Save the file to a location you can remember")
    print()
    print("STEP 2: Process the exported file")
    print("-" * 30)
    print("Run this script with the path to your ENEX file:")
    print()
    print("  python manual_export_guide.py /path/to/your/export.enex [format]")
    print()
    print("Formats: json (default), markdown")
    print()
    
    if len(sys.argv) > 1:
        enex_path = sys.argv[1]
        output_format = sys.argv[2] if len(sys.argv) > 2 else 'json'
        
        if os.path.exists(enex_path):
            process_enex_file(enex_path, output_format)
        else:
            print(f"❌ File not found: {enex_path}")
    else:
        print("Waiting for ENEX file path...")
        print()
        enex_path = input("Enter the path to your .enex file: ").strip()
        if enex_path and os.path.exists(enex_path):
            output_format = input("Enter output format (json/markdown) [default: json]: ").strip() or 'json'
            process_enex_file(enex_path, output_format)
        else:
            print("❌ Invalid file path")


if __name__ == "__main__":
    main()