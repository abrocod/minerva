import subprocess
import json
from datetime import datetime
from typing import List, Dict
import html
import re
from pathlib import Path
from minerva.directory_manager.directory_definition import EvernoteDirectory


class EvernoteExtractor:
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            evernote_dir = EvernoteDirectory()
            output_dir = evernote_dir.get_export_dir()
        self.output_dir = Path(output_dir)
        
    def _run_applescript(self, script: str) -> str:
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"AppleScript error: {e.stderr}")
            return ""
    
    def get_notebooks(self) -> List[str]:
        script = '''
        tell application "Evernote"
            set notebookList to {}
            set allNotebooks to every notebook
            repeat with nb in allNotebooks
                set end of notebookList to name of nb
            end repeat
            return notebookList
        end tell
        '''
        result = self._run_applescript(script)
        if result:
            notebooks = result.split(', ')
            return notebooks
        return []
    
    def get_notes_from_notebook(self, notebook_name: str) -> List[Dict]:
        # First get the note titles
        script = f'''
        tell application "Evernote"
            set notesList to {{}}
            try
                set targetNotebook to first notebook whose name is "{notebook_name}"
                set allNotes to every note of targetNotebook
                repeat with n in allNotes
                    set noteTitle to title of n
                    set end of notesList to noteTitle
                end repeat
            on error
                return "ERROR: Notebook not found"
            end try
            return notesList
        end tell
        '''
        
        titles_result = self._run_applescript(script)
        if titles_result.startswith("ERROR:") or not titles_result:
            return []
        
        note_titles = titles_result.split(', ') if titles_result else []
        notes = []
        
        # Get detailed info for each note
        for title in note_titles:
            if not title.strip():
                continue
                
            # Escape single quotes in title for AppleScript
            safe_title = title.replace("'", "\\'")
            detail_script = f'''
            tell application "Evernote"
                try
                    set targetNotebook to first notebook whose name is "{notebook_name}"
                    set targetNote to first note of targetNotebook whose title is "{safe_title}"
                    set noteContent to HTML content of targetNote
                    set noteCreated to creation date of targetNote
                    set noteModified to modification date of targetNote
                    return noteContent & "|||" & (noteCreated as string) & "|||" & (noteModified as string)
                on error
                    return ""
                end try
            end tell
            '''
            
            detail_result = self._run_applescript(detail_script)
            if detail_result:
                parts = detail_result.split('|||')
                if len(parts) >= 3:
                    note = {
                        'title': title,
                        'content_html': parts[0],
                        'created': parts[1],
                        'modified': parts[2],
                        'tags': ''
                    }
                    notes.append(note)
        
        return notes
    
    def _html_to_text(self, html_content: str) -> str:
        text = html.unescape(html_content)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def extract_notes(self, notebook_name: str, format: str = 'json') -> str:
        print(f"Extracting notes from notebook: {notebook_name}")
        
        notes = self.get_notes_from_notebook(notebook_name)
        
        if not notes:
            print(f"No notes found in notebook: {notebook_name}")
            return None
        
        print(f"Found {len(notes)} notes")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_notebook_name = re.sub(r'[^\w\s-]', '', notebook_name).strip().replace(' ', '_')
        
        if format == 'json':
            output_file = self.output_dir / f"{safe_notebook_name}_{timestamp}.json"
            
            for note in notes:
                note['content_text'] = self._html_to_text(note['content_html'])
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'notebook': notebook_name,
                    'export_date': datetime.now().isoformat(),
                    'note_count': len(notes),
                    'notes': notes
                }, f, indent=2, ensure_ascii=False)
                
        elif format == 'markdown':
            output_file = self.output_dir / f"{safe_notebook_name}_{timestamp}.md"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# {notebook_name}\n\n")
                f.write(f"Exported: {datetime.now().isoformat()}\n\n")
                f.write(f"Total notes: {len(notes)}\n\n")
                f.write("---\n\n")
                
                for i, note in enumerate(notes, 1):
                    f.write(f"## {i}. {note['title']}\n\n")
                    f.write(f"**Created:** {note['created']}\n")
                    f.write(f"**Modified:** {note['modified']}\n")
                    if note['tags']:
                        f.write(f"**Tags:** {note['tags']}\n")
                    f.write("\n")
                    
                    content_text = self._html_to_text(note['content_html'])
                    f.write(content_text)
                    f.write("\n\n---\n\n")
                    
        elif format == 'html':
            output_file = self.output_dir / f"{safe_notebook_name}_{timestamp}.html"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 40px; }}
        .note {{ margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .note-title {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
        .note-meta {{ color: #666; font-size: 14px; margin-bottom: 20px; }}
        .note-content {{ line-height: 1.6; }}
    </style>
</head>
<body>
    <h1>{}</h1>
    <p>Exported: {}</p>
    <p>Total notes: {}</p>
    <hr>
""".format(notebook_name, notebook_name, datetime.now().isoformat(), len(notes)))
                
                for note in notes:
                    f.write(f"""
    <div class="note">
        <div class="note-title">{note['title']}</div>
        <div class="note-meta">
            Created: {note['created']}<br>
            Modified: {note['modified']}<br>
            {'Tags: ' + note['tags'] if note['tags'] else ''}
        </div>
        <div class="note-content">
            {note['content_html']}
        </div>
    </div>
""")
                
                f.write("</body>\n</html>")
        
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'json', 'markdown', or 'html'")
        
        print(f"Notes exported to: {output_file}")
        return str(output_file)
    
    def list_all_notebooks(self) -> None:
        notebooks = self.get_notebooks()
        if notebooks:
            print(f"Found {len(notebooks)} notebooks:")
            for i, notebook in enumerate(notebooks, 1):
                print(f"  {i}. {notebook}")
        else:
            print("No notebooks found or unable to access Evernote")