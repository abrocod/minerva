#!/usr/bin/env python3
"""
Evernote Notes Extractor for Mac

This script extracts all notes from Evernote on Mac using AppleScript automation
and saves them locally in an organized folder structure.

Requirements:
- macOS with Evernote app installed
- Python 3.6+
- Evernote app must be running

Author: AI Assistant
"""

import argparse
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class EvernoteExtractor:
    """Extracts notes from Evernote using AppleScript automation."""
    
    def __init__(self, output_dir: str = "evernote_export"):
        """
        Initialize the Evernote extractor.
        
        Args:
            output_dir: Directory to save extracted notes
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.notes_dir = self.output_dir / "notes"
        self.metadata_dir = self.output_dir / "metadata"
        self.notes_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)
        
        self.extracted_notes: List[Dict] = []
        
    def _run_applescript(self, script: str) -> str:
        """
        Execute AppleScript and return the result.
        
        Args:
            script: AppleScript code to execute
            
        Returns:
            Script output as string
            
        Raises:
            RuntimeError: If AppleScript execution fails
        """
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"AppleScript execution failed: {e.stderr}")
    
    def _check_evernote_running(self) -> bool:
        """Check if Evernote is running."""
        script = '''
        tell application "System Events"
            return (name of processes) contains "Evernote"
        end tell
        '''
        try:
            result = self._run_applescript(script)
            return result.lower() == "true"
        except RuntimeError:
            return False
    
    def _get_notebooks(self) -> List[str]:
        """Get list of all notebooks from Evernote."""
        script = '''
        tell application "Evernote"
            set notebookList to {}
            repeat with nb in notebooks
                set end of notebookList to name of nb
            end repeat
            return notebookList
        end tell
        '''
        result = self._run_applescript(script)
        # Parse the AppleScript list format
        notebooks = [nb.strip() for nb in result.split(',') if nb.strip()]
        return notebooks
    
    def _get_notes_in_notebook(self, notebook_name: str) -> List[Dict]:
        """
        Get all notes in a specific notebook.
        
        Args:
            notebook_name: Name of the notebook
            
        Returns:
            List of note dictionaries with metadata
        """
        script = f'''
        tell application "Evernote"
            set noteList to {{}}
            set targetNotebook to notebook "{notebook_name}"
            repeat with n in notes of targetNotebook
                set noteInfo to {{}}
                set noteInfo to noteInfo & {{title of n}}
                set noteInfo to noteInfo & {{creation date of n as string}}
                set noteInfo to noteInfo & {{modification date of n as string}}
                set noteInfo to noteInfo & {{tag names of n as string}}
                set noteInfo to noteInfo & {{HTML content of n}}
                set end of noteList to noteInfo
            end repeat
            return noteList
        end tell
        '''
        
        try:
            result = self._run_applescript(script)
            return self._parse_notes_result(result, notebook_name)
        except RuntimeError as e:
            print(f"Warning: Could not extract notes from notebook '{notebook_name}': {e}")
            return []
    
    def _parse_notes_result(self, result: str, notebook_name: str) -> List[Dict]:
        """
        Parse the AppleScript result into note dictionaries.
        
        Args:
            result: Raw AppleScript output
            notebook_name: Name of the source notebook
            
        Returns:
            List of parsed note dictionaries
        """
        notes = []
        if not result or result == "{}":
            return notes
        
        # This is a simplified parser - AppleScript list parsing can be complex
        # In practice, you might need more robust parsing
        try:
            # Split by note boundaries (this is approximate)
            note_parts = result.split('}, {')
            
            for part in note_parts:
                # Clean up the part
                part = part.strip('{}')
                
                # Split into components (title, creation_date, mod_date, tags, content)
                components = part.split('", "')
                
                if len(components) >= 5:
                    note = {
                        'title': components[0].strip('"'),
                        'creation_date': components[1],
                        'modification_date': components[2],
                        'tags': components[3],
                        'content': components[4].strip('"'),
                        'notebook': notebook_name
                    }
                    notes.append(note)
        except Exception as e:
            print(f"Warning: Error parsing notes from {notebook_name}: {e}")
        
        return notes
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for filesystem compatibility.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = filename.strip()
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename or "untitled"
    
    def _save_note(self, note: Dict, note_index: int) -> None:
        """
        Save a single note to disk.
        
        Args:
            note: Note dictionary
            note_index: Index for unique filename generation
        """
        # Create notebook directory
        notebook_dir = self.notes_dir / self._sanitize_filename(note['notebook'])
        notebook_dir.mkdir(exist_ok=True)
        
        # Generate filename
        title = self._sanitize_filename(note['title'])
        filename = f"{note_index:04d}_{title}.html"
        filepath = notebook_dir / filename
        
        # Create HTML content with metadata
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{html.escape(note['title'])}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .metadata {{ background-color: #f5f5f5; padding: 10px; margin-bottom: 20px; border-radius: 5px; }}
        .content {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <div class="metadata">
        <h1>{html.escape(note['title'])}</h1>
        <p><strong>Notebook:</strong> {html.escape(note['notebook'])}</p>
        <p><strong>Created:</strong> {note['creation_date']}</p>
        <p><strong>Modified:</strong> {note['modification_date']}</p>
        <p><strong>Tags:</strong> {html.escape(note['tags'])}</p>
    </div>
    <div class="content">
        {note['content']}
    </div>
</body>
</html>"""
        
        # Save the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Saved: {filepath}")
    
    def _save_metadata(self) -> None:
        """Save extraction metadata to JSON file."""
        metadata = {
            'extraction_date': datetime.now().isoformat(),
            'total_notes': len(self.extracted_notes),
            'notebooks': list(set(note['notebook'] for note in self.extracted_notes)),
            'notes': self.extracted_notes
        }
        
        metadata_file = self.metadata_dir / "extraction_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Metadata saved: {metadata_file}")
    
    def extract_all_notes(self) -> None:
        """Extract all notes from Evernote."""
        print("Starting Evernote notes extraction...")
        
        # Check if Evernote is running
        if not self._check_evernote_running():
            print("Error: Evernote is not running. Please start Evernote and try again.")
            sys.exit(1)
        
        try:
            # Get all notebooks
            print("Getting list of notebooks...")
            notebooks = self._get_notebooks()
            print(f"Found {len(notebooks)} notebooks: {', '.join(notebooks)}")
            
            note_index = 0
            
            # Extract notes from each notebook
            for notebook in notebooks:
                print(f"\nExtracting notes from notebook: {notebook}")
                notes = self._get_notes_in_notebook(notebook)
                print(f"Found {len(notes)} notes in {notebook}")
                
                for note in notes:
                    self._save_note(note, note_index)
                    self.extracted_notes.append({
                        'index': note_index,
                        'title': note['title'],
                        'notebook': note['notebook'],
                        'creation_date': note['creation_date'],
                        'modification_date': note['modification_date'],
                        'tags': note['tags']
                    })
                    note_index += 1
            
            # Save metadata
            self._save_metadata()
            
            print(f"\nExtraction complete!")
            print(f"Total notes extracted: {len(self.extracted_notes)}")
            print(f"Notes saved to: {self.notes_dir}")
            print(f"Metadata saved to: {self.metadata_dir}")
            
        except Exception as e:
            print(f"Error during extraction: {e}")
            sys.exit(1)


def main():
    """Main function to run the Evernote extractor."""
    parser = argparse.ArgumentParser(description="Extract all notes from Evernote on Mac")
    parser.add_argument(
        "--output-dir", 
        default="evernote_export",
        help="Directory to save extracted notes (default: evernote_export)"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check if Evernote is running and list notebooks"
    )
    
    args = parser.parse_args()
    
    extractor = EvernoteExtractor(output_dir=args.output_dir)
    
    if args.check_only:
        if extractor._check_evernote_running():
            print("✓ Evernote is running")
            try:
                notebooks = extractor._get_notebooks()
                print(f"Found {len(notebooks)} notebooks:")
                for nb in notebooks:
                    print(f"  - {nb}")
            except Exception as e:
                print(f"Error getting notebooks: {e}")
        else:
            print("✗ Evernote is not running")
        return
    
    extractor.extract_all_notes()


if __name__ == "__main__":
    main() 