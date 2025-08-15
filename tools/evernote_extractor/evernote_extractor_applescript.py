#!/usr/bin/env python3
"""
Improved Evernote Notes Extractor for Mac

This version uses individual AppleScript calls for each note to avoid parsing issues
and provides better error handling and progress tracking.

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
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ImprovedEvernoteExtractor:
    """Improved Evernote extractor with better reliability."""
    
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
        self.logs_dir = self.output_dir / "logs"
        
        for dir_path in [self.notes_dir, self.metadata_dir, self.logs_dir]:
            dir_path.mkdir(exist_ok=True)
        
        self.extracted_notes: List[Dict] = []
        self.failed_notes: List[Dict] = []
        
        # Setup logging
        self.log_file = self.logs_dir / f"extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def _log(self, message: str) -> None:
        """Log message to both console and file."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')
    
    def _run_applescript(self, script: str, timeout: int = 30) -> str:
        """
        Execute AppleScript and return the result.
        
        Args:
            script: AppleScript code to execute
            timeout: Timeout in seconds
            
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
                check=True,
                timeout=timeout
            )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"AppleScript execution timed out after {timeout} seconds")
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
            set notebookNames to {}
            repeat with nb in notebooks
                set end of notebookNames to name of nb
            end repeat
            set AppleScript's text item delimiters to "|"
            set notebookString to notebookNames as string
            set AppleScript's text item delimiters to ""
            return notebookString
        end tell
        '''
        result = self._run_applescript(script)
        notebooks = [nb.strip() for nb in result.split('|') if nb.strip()]
        return notebooks
    
    def _get_note_count_in_notebook(self, notebook_name: str) -> int:
        """Get the number of notes in a notebook."""
        script = f'''
        tell application "Evernote"
            set targetNotebook to notebook "{notebook_name}"
            return count of notes of targetNotebook
        end tell
        '''
        try:
            result = self._run_applescript(script)
            return int(result)
        except (RuntimeError, ValueError):
            return 0
    
    def _get_note_titles_in_notebook(self, notebook_name: str) -> List[str]:
        """Get list of note titles in a notebook."""
        script = f'''
        tell application "Evernote"
            set targetNotebook to notebook "{notebook_name}"
            set noteTitles to {{}}
            repeat with n in notes of targetNotebook
                set end of noteTitles to title of n
            end repeat
            set AppleScript's text item delimiters to "|"
            set titleString to noteTitles as string
            set AppleScript's text item delimiters to ""
            return titleString
        end tell
        '''
        try:
            result = self._run_applescript(script)
            if not result:
                return []
            titles = [title.strip() for title in result.split('|') if title.strip()]
            return titles
        except RuntimeError:
            return []
    
    def _get_note_by_title(self, notebook_name: str, note_title: str) -> Optional[Dict]:
        """
        Get a specific note by title from a notebook.
        
        Args:
            notebook_name: Name of the notebook
            note_title: Title of the note
            
        Returns:
            Note dictionary or None if failed
        """
        # Escape quotes in the title for AppleScript
        escaped_title = note_title.replace('"', '\\"')
        escaped_notebook = notebook_name.replace('"', '\\"')
        
        script = f'''
        tell application "Evernote"
            set targetNotebook to notebook "{escaped_notebook}"
            set targetNote to first note of targetNotebook whose title is "{escaped_title}"
            
            set noteTitle to title of targetNote
            set noteCreated to creation date of targetNote as string
            set noteModified to modification date of targetNote as string
            set noteTags to tag names of targetNote
            set noteContent to HTML content of targetNote
            
            set AppleScript's text item delimiters to "|"
            set tagString to noteTags as string
            set AppleScript's text item delimiters to ""
            
            return noteTitle & "|||" & noteCreated & "|||" & noteModified & "|||" & tagString & "|||" & noteContent
        end tell
        '''
        
        try:
            result = self._run_applescript(script, timeout=60)
            
            # Parse the result
            parts = result.split('|||')
            if len(parts) >= 5:
                return {
                    'title': parts[0],
                    'creation_date': parts[1],
                    'modification_date': parts[2],
                    'tags': parts[3],
                    'content': '|||'.join(parts[4:]),  # Rejoin content in case it contains |||
                    'notebook': notebook_name
                }
        except RuntimeError as e:
            self._log(f"Failed to extract note '{note_title}' from '{notebook_name}': {e}")
            self.failed_notes.append({
                'title': note_title,
                'notebook': notebook_name,
                'error': str(e)
            })
        
        return None
    
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
    
    def _save_note(self, note: Dict, note_index: int) -> bool:
        """
        Save a single note to disk.
        
        Args:
            note: Note dictionary
            note_index: Index for unique filename generation
            
        Returns:
            True if successful, False otherwise
        """
        try:
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
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .metadata {{ 
            background-color: #f8f9fa; 
            padding: 15px; 
            margin-bottom: 20px; 
            border-radius: 8px; 
            border-left: 4px solid #007bff;
        }}
        .metadata h1 {{ margin-top: 0; color: #333; }}
        .metadata p {{ margin: 5px 0; color: #666; }}
        .content {{ 
            background-color: white; 
            padding: 20px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .tags {{ 
            background-color: #e9ecef; 
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.9em; 
        }}
    </style>
</head>
<body>
    <div class="metadata">
        <h1>{html.escape(note['title'])}</h1>
        <p><strong>📁 Notebook:</strong> {html.escape(note['notebook'])}</p>
        <p><strong>📅 Created:</strong> {note['creation_date']}</p>
        <p><strong>✏️ Modified:</strong> {note['modification_date']}</p>
        <p><strong>🏷️ Tags:</strong> <span class="tags">{html.escape(note['tags']) if note['tags'] else 'None'}</span></p>
    </div>
    <div class="content">
        {note['content']}
    </div>
</body>
</html>"""
            
            # Save the file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            self._log(f"Failed to save note '{note['title']}': {e}")
            return False
    
    def _save_metadata(self) -> None:
        """Save extraction metadata to JSON file."""
        metadata = {
            'extraction_date': datetime.now().isoformat(),
            'total_notes': len(self.extracted_notes),
            'failed_notes': len(self.failed_notes),
            'notebooks': list(set(note['notebook'] for note in self.extracted_notes)),
            'notes': self.extracted_notes,
            'failed_extractions': self.failed_notes
        }
        
        metadata_file = self.metadata_dir / "extraction_metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self._log(f"Metadata saved: {metadata_file}")
    
    def extract_all_notes(self) -> None:
        """Extract all notes from Evernote."""
        self._log("Starting Evernote notes extraction...")
        
        # Check if Evernote is running
        if not self._check_evernote_running():
            self._log("Error: Evernote is not running. Please start Evernote and try again.")
            sys.exit(1)
        
        try:
            # Get all notebooks
            self._log("Getting list of notebooks...")
            notebooks = self._get_notebooks()
            self._log(f"Found {len(notebooks)} notebooks: {', '.join(notebooks)}")
            
            note_index = 0
            total_notes = 0
            
            # Count total notes first
            for notebook in notebooks:
                count = self._get_note_count_in_notebook(notebook)
                total_notes += count
                self._log(f"Notebook '{notebook}': {count} notes")
            
            self._log(f"Total notes to extract: {total_notes}")
            
            # Extract notes from each notebook
            for notebook_idx, notebook in enumerate(notebooks, 1):
                self._log(f"\n[{notebook_idx}/{len(notebooks)}] Processing notebook: {notebook}")
                
                # Get all note titles in this notebook
                note_titles = self._get_note_titles_in_notebook(notebook)
                self._log(f"Found {len(note_titles)} notes in {notebook}")
                
                # Extract each note individually
                for note_idx, note_title in enumerate(note_titles, 1):
                    self._log(f"  [{note_idx}/{len(note_titles)}] Extracting: {note_title[:50]}...")
                    
                    note = self._get_note_by_title(notebook, note_title)
                    if note:
                        if self._save_note(note, note_index):
                            self.extracted_notes.append({
                                'index': note_index,
                                'title': note['title'],
                                'notebook': note['notebook'],
                                'creation_date': note['creation_date'],
                                'modification_date': note['modification_date'],
                                'tags': note['tags']
                            })
                            note_index += 1
                    
                    # Small delay to avoid overwhelming Evernote
                    time.sleep(0.1)
            
            # Save metadata
            self._save_metadata()
            
            self._log(f"\n✅ Extraction complete!")
            self._log(f"📊 Total notes extracted: {len(self.extracted_notes)}")
            self._log(f"❌ Failed extractions: {len(self.failed_notes)}")
            self._log(f"📁 Notes saved to: {self.notes_dir}")
            self._log(f"📋 Metadata saved to: {self.metadata_dir}")
            self._log(f"📝 Log saved to: {self.log_file}")
            
        except Exception as e:
            self._log(f"Error during extraction: {e}")
            sys.exit(1)


def main():
    """Main function to run the improved Evernote extractor."""
    parser = argparse.ArgumentParser(description="Extract all notes from Evernote on Mac (Improved Version)")
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
    
    extractor = ImprovedEvernoteExtractor(output_dir=args.output_dir)
    
    if args.check_only:
        if extractor._check_evernote_running():
            print("✅ Evernote is running")
            try:
                notebooks = extractor._get_notebooks()
                print(f"Found {len(notebooks)} notebooks:")
                for nb in notebooks:
                    count = extractor._get_note_count_in_notebook(nb)
                    print(f"  📁 {nb} ({count} notes)")
            except Exception as e:
                print(f"Error getting notebooks: {e}")
        else:
            print("❌ Evernote is not running")
        return
    
    extractor.extract_all_notes()


if __name__ == "__main__":
    main() 