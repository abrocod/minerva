#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from minerva.tools.evernote_extractor.enex_parser import ENEXParser
from minerva.directory_manager.directory_definition import EvernoteDirectory
from pathlib import Path
import json
import re
from datetime import datetime


class IndividualNoteExporter:
    """Export each note from ENEX file as a separate markdown file"""
    
    def __init__(self):
        self.parser = ENEXParser()
        evernote_dir = EvernoteDirectory()
        self.output_base_dir = Path(evernote_dir.get_export_dir())
    
    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """Create a safe filename from note title"""
        # Remove or replace invalid characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        
        # Limit length
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length].strip()
        
        # Ensure it's not empty
        if not safe_title:
            safe_title = "Untitled"
            
        return safe_title
    
    def export_notes_individually(self, enex_file_path: str) -> str:
        """Export each note as a separate markdown file"""
        
        print(f"Processing ENEX file: {enex_file_path}")
        
        # Parse the ENEX file
        notes = self.parser.parse_enex_file(enex_file_path)
        print(f"Found {len(notes)} notes")
        
        # Create output directory for this notebook
        notebook_name = Path(enex_file_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.output_base_dir / f"{notebook_name}_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index file
        index_content = f"# {notebook_name}\n\n"
        index_content += f"Exported: {datetime.now().isoformat()}\n"
        index_content += f"Total notes: {len(notes)}\n\n"
        index_content += "## Notes Index\n\n"
        
        # Export each note
        for i, note in enumerate(notes, 1):
            # Generate filename
            title = note.get('title', 'Untitled')
            safe_title = self.sanitize_filename(title)
            filename = f"{i:04d}_{safe_title}.md"
            file_path = output_dir / filename
            
            # Write note content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                
                # Metadata
                if 'created' in note:
                    f.write(f"**Created:** {note['created']}  \n")
                if 'modified' in note:
                    f.write(f"**Modified:** {note['modified']}  \n")
                if note.get('tags'):
                    f.write(f"**Tags:** {', '.join(note['tags'])}  \n")
                f.write("\n---\n\n")
                
                # Content
                content = note.get('content_text', '')
                if not content and 'content_html' in note:
                    content = self.parser._html_to_text(note['content_html'])
                f.write(content)
                
                # Resources/Attachments
                if note.get('resources'):
                    f.write("\n\n---\n\n")
                    f.write("## Attachments\n\n")
                    for resource in note['resources']:
                        if 'filename' in resource:
                            f.write(f"- {resource['filename']}")
                            if 'mime' in resource:
                                f.write(f" ({resource['mime']})")
                            if 'size' in resource:
                                f.write(f" - {resource['size']:,} bytes")
                            f.write("\n")
            
            # Add to index
            index_content += f"{i}. [{title}]({filename})"
            if note.get('tags'):
                index_content += f" - *Tags: {', '.join(note['tags'])}*"
            index_content += "\n"
            
            if i % 10 == 0:
                print(f"  Processed {i}/{len(notes)} notes...")
        
        # Write index file
        index_path = output_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        # Create metadata JSON
        metadata = {
            'notebook_name': notebook_name,
            'export_date': datetime.now().isoformat(),
            'note_count': len(notes),
            'output_directory': str(output_dir),
            'notes_summary': [
                {
                    'index': i,
                    'title': note.get('title', 'Untitled'),
                    'created': note.get('created', ''),
                    'modified': note.get('modified', ''),
                    'tags': note.get('tags', []),
                    'has_attachments': bool(note.get('resources'))
                }
                for i, note in enumerate(notes, 1)
            ]
        }
        
        metadata_path = output_dir / "metadata.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Successfully exported {len(notes)} notes to: {output_dir}")
        print(f"   - Each note saved as individual markdown file")
        print(f"   - Index available at: {index_path}")
        print(f"   - Metadata saved to: {metadata_path}")
        
        return str(output_dir)


def main():
    if len(sys.argv) < 2:
        print("Usage: python enex_to_individual_notes.py <path_to_enex_file>")
        print("\nThis script will:")
        print("1. Parse the ENEX file")
        print("2. Create a new directory for the notebook")
        print("3. Save each note as a separate markdown file")
        print("4. Generate an index file (README.md) with links to all notes")
        print("5. Create a metadata.json file with summary information")
        sys.exit(1)
    
    enex_path = sys.argv[1]
    
    if not os.path.exists(enex_path):
        print(f"❌ File not found: {enex_path}")
        sys.exit(1)
    
    exporter = IndividualNoteExporter()
    exporter.export_notes_individually(enex_path)


if __name__ == "__main__":
    main()