import xml.etree.ElementTree as ET
import base64
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json
import html


class ENEXParser:
    """
    Parser for Evernote Export Format (ENEX) files.
    ENEX files are XML-based exports from Evernote.
    """
    
    def __init__(self):
        self.notes = []
        
    def parse_enex_file(self, file_path: str) -> List[Dict]:
        """Parse an ENEX file and extract notes"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        notes = []
        for note_elem in root.findall('note'):
            note = self._parse_note(note_elem)
            if note:
                notes.append(note)
        
        return notes
    
    def _parse_note(self, note_elem) -> Dict:
        """Parse a single note element"""
        note = {}
        
        # Extract title
        title_elem = note_elem.find('title')
        note['title'] = title_elem.text if title_elem is not None else 'Untitled'
        
        # Extract content
        content_elem = note_elem.find('content')
        if content_elem is not None:
            note['content_html'] = content_elem.text
            note['content_text'] = self._html_to_text(content_elem.text)
        else:
            note['content_html'] = ''
            note['content_text'] = ''
        
        # Extract dates
        created_elem = note_elem.find('created')
        if created_elem is not None:
            note['created'] = self._parse_date(created_elem.text)
        
        updated_elem = note_elem.find('updated')
        if updated_elem is not None:
            note['modified'] = self._parse_date(updated_elem.text)
        
        # Extract tags
        tags = []
        for tag_elem in note_elem.findall('tag'):
            if tag_elem.text:
                tags.append(tag_elem.text)
        note['tags'] = tags
        
        # Extract attributes
        attrs = note_elem.find('note-attributes')
        if attrs is not None:
            note['attributes'] = self._parse_attributes(attrs)
        
        # Extract resources (attachments)
        resources = []
        for resource_elem in note_elem.findall('resource'):
            resource = self._parse_resource(resource_elem)
            if resource:
                resources.append(resource)
        note['resources'] = resources
        
        return note
    
    def _parse_date(self, date_str: str) -> str:
        """Parse Evernote date format (YYYYMMDDTHHMMSSz)"""
        try:
            # Evernote format: 20240115T120000Z
            dt = datetime.strptime(date_str[:15], '%Y%m%dT%H%M%S')
            return dt.isoformat()
        except:
            return date_str
    
    def _parse_attributes(self, attrs_elem) -> Dict:
        """Parse note attributes"""
        attrs = {}
        for child in attrs_elem:
            if child.text:
                attrs[child.tag] = child.text
        return attrs
    
    def _parse_resource(self, resource_elem) -> Dict:
        """Parse a resource (attachment)"""
        resource = {}
        
        # Get MIME type
        mime_elem = resource_elem.find('mime')
        if mime_elem is not None:
            resource['mime'] = mime_elem.text
        
        # Get file name if available
        attrs = resource_elem.find('resource-attributes')
        if attrs is not None:
            filename_elem = attrs.find('file-name')
            if filename_elem is not None:
                resource['filename'] = filename_elem.text
        
        # Get data size
        data_elem = resource_elem.find('data')
        if data_elem is not None:
            encoding = data_elem.get('encoding')
            if encoding == 'base64' and data_elem.text:
                resource['size'] = len(base64.b64decode(data_elem.text))
            
        return resource
    
    def _html_to_text(self, html_content: str) -> str:
        """Convert HTML/ENML content to plain text"""
        if not html_content:
            return ''
        
        # Remove CDATA wrapper if present
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', html_content, flags=re.DOTALL)
        
        # Convert special tags
        text = re.sub(r'<en-note[^>]*>', '', text)
        text = re.sub(r'</en-note>', '', text)
        text = re.sub(r'<en-media[^>]*/?>', '[Attachment]', text)
        
        # Convert HTML to text
        text = html.unescape(text)
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def export_to_json(self, notes: List[Dict], output_path: str) -> None:
        """Export parsed notes to JSON"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'export_date': datetime.now().isoformat(),
                'note_count': len(notes),
                'notes': notes
            }, f, indent=2, ensure_ascii=False)
    
    def export_to_markdown(self, notes: List[Dict], output_path: str) -> None:
        """Export parsed notes to Markdown"""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# Evernote Export\n\n")
            f.write(f"Exported: {datetime.now().isoformat()}\n\n")
            f.write(f"Total notes: {len(notes)}\n\n")
            f.write("---\n\n")
            
            for i, note in enumerate(notes, 1):
                f.write(f"## {i}. {note['title']}\n\n")
                if 'created' in note:
                    f.write(f"**Created:** {note['created']}\n")
                if 'modified' in note:
                    f.write(f"**Modified:** {note['modified']}\n")
                if note.get('tags'):
                    f.write(f"**Tags:** {', '.join(note['tags'])}\n")
                f.write("\n")
                f.write(note.get('content_text', ''))
                f.write("\n\n---\n\n")