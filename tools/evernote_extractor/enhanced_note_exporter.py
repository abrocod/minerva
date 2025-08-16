#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

import xml.etree.ElementTree as ET
import base64
import hashlib
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json
from minerva.directory_manager.directory_definition import EvernoteDirectory


class EnhancedNoteExporter:
    """Export notes with embedded image references and extracted attachments"""
    
    def __init__(self):
        evernote_dir = EvernoteDirectory()
        self.output_base_dir = Path(evernote_dir.get_export_dir())
    
    def sanitize_filename(self, title: str, max_length: int = 100) -> str:
        """Create a safe filename from note title"""
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        safe_title = re.sub(r'\s+', ' ', safe_title).strip()
        
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length].strip()
        
        if not safe_title:
            safe_title = "Untitled"
            
        return safe_title
    
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
    
    def _extract_resource(self, resource_elem, attachments_dir: Path, note_idx: int) -> Dict:
        """Extract a single resource/attachment"""
        
        # Get data
        data_elem = resource_elem.find('data')
        if data_elem is None or not data_elem.text:
            return None
        
        encoding = data_elem.get('encoding', '')
        if encoding != 'base64':
            return None
        
        try:
            attachment_data = base64.b64decode(data_elem.text)
        except Exception:
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
        
        # Get resource hash from the ENEX (used to link in content)
        resource_hash = None
        recognition_elem = resource_elem.find('recognition')
        if recognition_elem is not None:
            # Try to extract hash from recognition data
            pass
        
        # Use the data hash from resource element if available
        data_hash_elem = resource_elem.find('data')
        if data_hash_elem is not None:
            resource_hash = data_hash_elem.get('hash')
        
        attachment_info = {
            'hash': data_hash,
            'resource_hash': resource_hash,
            'filename': filename,
            'original_filename': attrs.find('file-name').text if attrs is not None and attrs.find('file-name') is not None else None,
            'mime_type': mime_type,
            'size': len(attachment_data),
            'file_path': str(file_path),
            'relative_path': f"attachments/{filename}",
            'note_index': note_idx,
            'is_image': mime_type.startswith('image/')
        }
        
        return attachment_info
    
    def _html_to_markdown_with_images(self, html_content: str, resources: List[Dict]) -> str:
        """Convert HTML/ENML content to markdown with embedded images"""
        if not html_content:
            return ''
        
        # Create resource hash lookup
        resource_lookup = {}
        for resource in resources:
            if resource.get('resource_hash'):
                resource_lookup[resource['resource_hash']] = resource
        
        # Remove CDATA wrapper if present
        text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', html_content, flags=re.DOTALL)
        
        # Handle en-media tags (Evernote attachments)
        def replace_media(match):
            media_tag = match.group(0)
            # Extract hash from the en-media tag
            hash_match = re.search(r'hash="([^"]+)"', media_tag)
            if hash_match:
                resource_hash = hash_match.group(1)
                if resource_hash in resource_lookup:
                    resource = resource_lookup[resource_hash]
                    if resource['is_image']:
                        # Create markdown image reference
                        alt_text = resource.get('original_filename', 'Image')
                        return f"\n\n![{alt_text}]({resource['relative_path']})\n\n"
                    else:
                        # Create markdown link for non-image attachments
                        link_text = resource.get('original_filename', 'Attachment')
                        return f"\n\n[📎 {link_text}]({resource['relative_path']})\n\n"
            
            # Fallback for unmatched media
            return '\n\n[Attachment]\n\n'
        
        text = re.sub(r'<en-media[^>]*/?>', replace_media, text)
        
        # Convert other ENML/HTML tags
        text = re.sub(r'<en-note[^>]*>', '', text)
        text = re.sub(r'</en-note>', '', text)
        
        # Convert HTML to markdown-like format
        text = re.sub(r'<br\s*/?>', '\n', text)
        text = re.sub(r'<p[^>]*>', '\n\n', text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'<div[^>]*>', '\n\n', text)
        text = re.sub(r'</div>', '\n\n', text)
        
        # Handle headings
        text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'\n\n# \1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n\n## \1\n\n', text, flags=re.DOTALL)
        text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n\n### \1\n\n', text, flags=re.DOTALL)
        
        # Handle formatting
        text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text, flags=re.DOTALL)
        text = re.sub(r'<b[^>]*>(.*?)</b>', r'**\1**', text, flags=re.DOTALL)
        text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text, flags=re.DOTALL)
        text = re.sub(r'<i[^>]*>(.*?)</i>', r'*\1*', text, flags=re.DOTALL)
        
        # Handle links
        text = re.sub(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text, flags=re.DOTALL)
        
        # Handle lists
        text = re.sub(r'<ul[^>]*>', '\n', text)
        text = re.sub(r'</ul>', '\n', text)
        text = re.sub(r'<ol[^>]*>', '\n', text)
        text = re.sub(r'</ol>', '\n', text)
        text = re.sub(r'<li[^>]*>', '\n- ', text)
        text = re.sub(r'</li>', '', text)
        
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Clean up excessive whitespace
        text = re.sub(r'\n{4,}', '\n\n\n', text)
        text = re.sub(r'[ \t]+\n', '\n', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        return text.strip()
    
    def export_notes_with_images(self, enex_file_path: str) -> str:
        """Export each note as a separate markdown file with embedded images"""
        
        print(f"Processing ENEX file: {enex_file_path}")
        
        # Parse the ENEX file
        tree = ET.parse(enex_file_path)
        root = tree.getroot()
        
        # Create output directory for this notebook
        notebook_name = Path(enex_file_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.output_base_dir / f"{notebook_name}_with_images_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create attachments subdirectory
        attachments_dir = output_dir / "attachments"
        attachments_dir.mkdir(exist_ok=True)
        
        # Create index file
        index_content = f"# {notebook_name}\n\n"
        index_content += f"Exported: {datetime.now().isoformat()}\n"
        index_content += "## Notes with Embedded Images\n\n"
        
        note_count = 0
        
        # Process each note
        for note_idx, note_elem in enumerate(root.findall('note'), 1):
            # Extract note data
            title_elem = note_elem.find('title')
            title = title_elem.text if title_elem is not None else 'Untitled'
            
            content_elem = note_elem.find('content')
            content_html = content_elem.text if content_elem is not None else ''
            
            # Extract dates
            created_elem = note_elem.find('created')
            created = self._parse_date(created_elem.text) if created_elem is not None else ''
            
            updated_elem = note_elem.find('updated')
            modified = self._parse_date(updated_elem.text) if updated_elem is not None else ''
            
            # Extract tags
            tags = []
            for tag_elem in note_elem.findall('tag'):
                if tag_elem.text:
                    tags.append(tag_elem.text)
            
            # Extract resources/attachments
            resources = []
            for resource_elem in note_elem.findall('resource'):
                resource = self._extract_resource(resource_elem, attachments_dir, note_idx)
                if resource:
                    resources.append(resource)
            
            # Generate filename
            safe_title = self.sanitize_filename(title)
            filename = f"{note_idx:04d}_{safe_title}.md"
            file_path = output_dir / filename
            
            # Convert content to markdown with embedded images
            content_markdown = self._html_to_markdown_with_images(content_html, resources)
            
            # Write note file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# {title}\n\n")
                
                # Metadata
                if created:
                    f.write(f"**Created:** {created}  \n")
                if modified:
                    f.write(f"**Modified:** {modified}  \n")
                if tags:
                    f.write(f"**Tags:** {', '.join(tags)}  \n")
                f.write("\n---\n\n")
                
                # Content with embedded images
                f.write(content_markdown)
                
                # Additional attachments (non-images)
                non_image_resources = [r for r in resources if not r['is_image']]
                if non_image_resources:
                    f.write("\n\n---\n\n")
                    f.write("## Additional Attachments\n\n")
                    for resource in non_image_resources:
                        f.write(f"- [📎 {resource.get('original_filename', 'Attachment')}]({resource['relative_path']})")
                        if 'mime_type' in resource:
                            f.write(f" ({resource['mime_type']})")
                        if 'size' in resource:
                            f.write(f" - {resource['size']:,} bytes")
                        f.write("\n")
            
            # Add to index
            index_content += f"{note_idx}. [{title}]({filename})"
            if tags:
                index_content += f" - *Tags: {', '.join(tags)}*"
            if resources:
                image_count = len([r for r in resources if r['is_image']])
                if image_count > 0:
                    index_content += f" - 🖼️ {image_count} image(s)"
            index_content += "\n"
            
            note_count += 1
            if note_count % 10 == 0:
                print(f"  Processed {note_count} notes...")
        
        # Update index header
        index_content = index_content.replace("## Notes with Embedded Images\n\n", 
                                            f"Total notes: {note_count}\n\n## Notes with Embedded Images\n\n")
        
        # Write index file
        index_path = output_dir / "README.md"
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        print(f"\n✅ Successfully exported {note_count} notes with embedded images to: {output_dir}")
        print(f"   - Images are embedded directly in markdown files")
        print(f"   - Attachments saved to: {attachments_dir}")
        print(f"   - Index available at: {index_path}")
        
        return str(output_dir)
    
    def _parse_date(self, date_str: str) -> str:
        """Parse Evernote date format"""
        try:
            dt = datetime.strptime(date_str[:15], '%Y%m%dT%H%M%S')
            return dt.isoformat()
        except:
            return date_str


def main():
    if len(sys.argv) < 2:
        print("Usage: python enhanced_note_exporter.py <path_to_enex_file>")
        print("\nThis script will:")
        print("1. Parse the ENEX file")
        print("2. Extract all attachments")
        print("3. Create markdown files with embedded image references")
        print("4. Images will display directly in markdown viewers")
        sys.exit(1)
    
    enex_path = sys.argv[1]
    
    if not os.path.exists(enex_path):
        print(f"❌ File not found: {enex_path}")
        sys.exit(1)
    
    exporter = EnhancedNoteExporter()
    exporter.export_notes_with_images(enex_path)


if __name__ == "__main__":
    main()