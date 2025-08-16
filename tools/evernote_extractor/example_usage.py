#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from minerva.tools.evernote_extractor import EvernoteExtractor


def main():
    extractor = EvernoteExtractor()
    
    print("Evernote Note Extractor")
    print("-" * 50)
    
    extractor.list_all_notebooks()
    print("-" * 50)
    
    if len(sys.argv) > 1:
        notebook_name = sys.argv[1]
        format_type = sys.argv[2] if len(sys.argv) > 2 else 'json'
    else:
        notebook_name = input("\nEnter notebook name to extract: ")
        format_type = input("Enter export format (json/markdown/html) [default: json]: ").strip() or 'json'
    
    if notebook_name:
        output_file = extractor.extract_notes(notebook_name, format=format_type)
        if output_file:
            print(f"\n✅ Successfully exported notes to: {output_file}")
        else:
            print(f"\n❌ Failed to export notes from notebook: {notebook_name}")
    else:
        print("No notebook name provided")


if __name__ == "__main__":
    main()