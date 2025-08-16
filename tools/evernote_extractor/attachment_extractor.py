#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import xml.etree.ElementTree as ET
import base64
import hashlib
from pathlib import Path
from typing import Dict, List
from minerva.directory_manager.directory_definition import EvernoteDirectory


class AttachmentExtractor:
    """Extract attachments from ENEX files"""
    
    def __init__(self):
        evernote_dir = EvernoteDirectory()
        self.output_base_dir = Path(evernote_dir.get_export_dir())
    
    def extract_attachments_from_enex(self, enex_file_path: str, notebook_dir: str) -> Dict:
        """Extract all attachments from an ENEX file"""
        
        tree = ET.parse(enex_file_path)
        root = tree.getroot()
        
        # Create attachments directory
        attachments_dir = Path(notebook_dir) / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        
        attachment_map = {}  # Maps hash to file info
        note_attachments = {}  # Maps note index to attachment list
        
        for note_idx, note_elem in enumerate(root.findall('note'), 1):
            note_title = note_elem.find('title')
            note_title = note_title.text if note_title is not None else f"Note_{note_idx}"
            
            attachments = []
            
            # Find all resources in this note
            for resource_elem in note_elem.findall('resource'):
                attachment_info = self._extract_resource(resource_elem, attachments_dir, note_idx)
                if attachment_info:
                    attachments.append(attachment_info)
                    attachment_map[attachment_info['hash']] = attachment_info
            
            if attachments:
                note_attachments[note_idx] = {
                    'title': note_title,
                    'attachments': attachments
                }
        
        print(f"\n📎 Extracted {len(attachment_map)} unique attachments")
        print(f"   Saved to: {attachments_dir}")
        
        # Create attachment index
        self._create_attachment_index(attachments_dir, note_attachments)
        
        return {
            'attachment_map': attachment_map,
            'note_attachments': note_attachments,
            'attachments_dir': str(attachments_dir)
        }
    
    def _extract_resource(self, resource_elem, attachments_dir: Path, note_idx: int) -> Dict:
        """Extract a single resource/attachment"""
        
        # Get data
        data_elem = resource_elem.find('data')
        if data_elem is None or not data_elem.text:
            return None
        
        encoding = data_elem.get('encoding', '')
        if encoding != 'base64':
            print(f"Warning: Unsupported encoding '{encoding}' for attachment in note {note_idx}")
            return None
        
        try:
            # Decode base64 data
            attachment_data = base64.b64decode(data_elem.text)
        except Exception as e:
            print(f"Error decoding attachment in note {note_idx}: {e}")
            return None
        
        # Get hash for deduplication
        data_hash = hashlib.md5(attachment_data).hexdigest()[:8]
        
        # Get MIME type
        mime_elem = resource_elem.find('mime')
        mime_type = mime_elem.text if mime_elem is not None else 'application/octet-stream'
        
        # Get filename from attributes
        filename = None
        attrs = resource_elem.find('resource-attributes')
        if attrs is not None:
            filename_elem = attrs.find('file-name')
            if filename_elem is not None:
                filename = filename_elem.text
        
        # Generate filename if not provided
        if not filename:
            ext = self._get_extension_from_mime(mime_type)
            filename = f"{data_hash}{ext}"
        else:
            # Clean and truncate filename
            clean_filename = filename.replace('\n', '').replace('\r', '').strip()
            # Truncate if too long
            if len(clean_filename) > 50:
                name_parts = clean_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    clean_filename = f"{name_parts[0][:40]}.{name_parts[1]}"
                else:
                    clean_filename = clean_filename[:50]
            
            # Add hash prefix to avoid conflicts
            name_parts = clean_filename.rsplit('.', 1)
            if len(name_parts) == 2:
                filename = f"{data_hash}_{name_parts[0]}.{name_parts[1]}"
            else:
                filename = f"{data_hash}_{clean_filename}"
        
        # Save file
        file_path = attachments_dir / filename
        with open(file_path, 'wb') as f:
            f.write(attachment_data)
        
        attachment_info = {
            'hash': data_hash,
            'filename': filename,
            'original_filename': attrs.find('file-name').text if attrs is not None and attrs.find('file-name') is not None else None,
            'mime_type': mime_type,
            'size': len(attachment_data),
            'file_path': str(file_path),
            'note_index': note_idx
        }
        
        return attachment_info
    
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/svg+xml': '.svg',
            'image/webp': '.webp',
            'application/pdf': '.pdf',
            'text/plain': '.txt',
            'text/html': '.html',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/zip': '.zip',
            'audio/mpeg': '.mp3',
            'video/mp4': '.mp4',
        }
        return mime_to_ext.get(mime_type, '.bin')
    
    def _create_attachment_index(self, attachments_dir: Path, note_attachments: Dict):
        """Create an index of all attachments"""
        
        index_content = "# Attachments Index\n\n"
        index_content += f"Total attachments: {sum(len(info['attachments']) for info in note_attachments.values())}\n\n"
        
        for note_idx, info in note_attachments.items():
            index_content += f"## Note {note_idx:04d}: {info['title']}\n\n"
            
            for attachment in info['attachments']:
                index_content += f"- **{attachment['filename']}**\n"
                index_content += f"  - Type: {attachment['mime_type']}\n"
                index_content += f"  - Size: {attachment['size']:,} bytes\n"
                if attachment['original_filename']:
                    index_content += f"  - Original: {attachment['original_filename']}\n"
                index_content += f"  - Hash: {attachment['hash']}\n"
                index_content += "\n"
        
        index_path = attachments_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)


def main():
    if len(sys.argv) < 2:
        print("Usage: python attachment_extractor.py <enex_file_path> [notebook_directory]")
        print("\nExtracts all attachments from an ENEX file")
        sys.exit(1)
    
    enex_path = sys.argv[1]
    
    if not os.path.exists(enex_path):
        print(f"❌ File not found: {enex_path}")
        sys.exit(1)
    
    # Determine notebook directory
    if len(sys.argv) > 2:
        notebook_dir = sys.argv[2]
    else:
        # Try to find the corresponding notebook directory
        evernote_dir = EvernoteDirectory()
        export_dir = Path(evernote_dir.get_export_dir())
        enex_name = Path(enex_path).stem
        
        # Look for existing notebook directory
        possible_dirs = list(export_dir.glob(f"{enex_name}_*"))
        if possible_dirs:
            notebook_dir = str(possible_dirs[0])
            print(f"Found existing notebook directory: {notebook_dir}")
        else:
            print(f"❌ Could not find notebook directory for {enex_name}")
            print(f"Please specify the notebook directory as second argument")
            sys.exit(1)
    
    extractor = AttachmentExtractor()
    result = extractor.extract_attachments_from_enex(enex_path, notebook_dir)
    
    print(f"\n✅ Attachment extraction complete!")
    print(f"   Attachments saved to: {result['attachments_dir']}")


if __name__ == "__main__":
    main()