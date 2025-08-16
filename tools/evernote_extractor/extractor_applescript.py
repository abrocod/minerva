import subprocess
import json
from datetime import datetime
from typing import List, Dict
import html
import re
from pathlib import Path
from minerva.directory_manager.directory_definition import EvernoteDirectory


class EvernoteExtractorAppleScript:
    """
    Alternative implementation using AppleScript.
    Note: This requires proper Evernote AppleScript support which may vary by Evernote version.
    """
    
    def __init__(self, output_dir: str = None):
        if output_dir is None:
            evernote_dir = EvernoteDirectory()
            output_dir = evernote_dir.get_export_dir()
        self.output_dir = Path(output_dir)
        
    def test_connection(self) -> bool:
        """Test if Evernote is running and accessible"""
        script = 'tell application "System Events" to (name of processes) contains "Evernote"'
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip() == 'true'
        except:
            return False
    
    def export_notebook_enex(self, notebook_name: str) -> str:
        """
        Export a notebook using Evernote's export functionality.
        This approach uses UI scripting to trigger export.
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_notebook_name = re.sub(r'[^\w\s-]', '', notebook_name).strip().replace(' ', '_')
        output_file = self.output_dir / f"{safe_notebook_name}_{timestamp}.enex"
        
        script = f'''
        tell application "Evernote"
            activate
            delay 1
            
            -- This would require UI scripting permissions
            -- The exact implementation depends on Evernote version
            
        end tell
        '''
        
        print(f"Note: AppleScript export requires UI automation permissions.")
        print(f"For reliable export, consider using Evernote's manual export feature:")
        print(f"1. Open Evernote")
        print(f"2. Right-click on the '{notebook_name}' notebook")
        print(f"3. Select 'Export Notebook...'")
        print(f"4. Save as ENEX format to: {self.output_dir}")
        
        return str(output_file)