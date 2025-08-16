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


class FinalImageEmbedder:
    """Final version that properly embeds images in markdown files"""
    
    def __init__(self):
        evernote_dir = EvernoteDirectory()
        self.output_base_dir = Path(evernote_dir.get_export_dir())
    
    def process_existing_export(self, notes_dir: str, attachments_dir: str) -> str:
        """Process existing exported notes and embed images"""
        
        notes_path = Path(notes_dir)
        attachments_path = Path(attachments_dir)
        
        if not notes_path.exists() or not attachments_path.exists():
            print(f"❌ Directory not found: {notes_path} or {attachments_path}")
            return None
        
        # Create new output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.output_base_dir / f"with_embedded_images_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy attachments directory
        import shutil
        new_attachments_dir = output_dir / "attachments"
        shutil.copytree(attachments_path, new_attachments_dir)
        
        # Get list of image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'}
        image_files = {}
        
        for file_path in new_attachments_dir.iterdir():
            if file_path.suffix.lower() in image_extensions:
                # Extract potential original name from filename
                filename = file_path.name
                if '_' in filename:
                    # Format: hash_originalname.ext
                    original_name = '_'.join(filename.split('_')[1:])
                    image_files[original_name] = filename
                    # Also map the hash part
                    hash_part = filename.split('_')[0]
                    image_files[hash_part] = filename
                image_files[filename] = filename
        
        print(f"Found {len(image_files)} image mappings")
        
        # Process each markdown file
        processed_count = 0
        for md_file in notes_path.glob("*.md"):
            if md_file.name == "README.md":
                continue
                
            # Read the original file
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Replace [Attachment] with actual image references
            new_content = self._embed_images_in_content(content, image_files)
            
            # Write to new location
            new_file_path = output_dir / md_file.name
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"  Processed {processed_count} files...")
        
        # Create index
        self._create_index(output_dir, processed_count)
        
        print(f"\n✅ Successfully processed {processed_count} notes with embedded images")
        print(f"   Output directory: {output_dir}")
        
        return str(output_dir)
    
    def _embed_images_in_content(self, content: str, image_files: Dict) -> str:
        """Replace [Attachment] markers with actual image embeddings"""
        
        lines = content.split('\n')
        new_lines = []
        
        for i, line in enumerate(lines):
            if '[Attachment]' in line:
                # Look for context clues about what image this might be
                # Check surrounding lines for hints
                context_lines = []
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    context_lines.append(lines[j])
                
                context = ' '.join(context_lines).lower()
                
                # Try to find a matching image
                image_found = False
                for original_name, filename in image_files.items():
                    # Skip if already processed
                    if filename in content:
                        continue
                        
                    # Simple heuristic: if this is the first unmatched image, use it
                    if not image_found:
                        relative_path = f"attachments/{filename}"
                        alt_text = original_name.replace('_', ' ').replace('-', ' ')
                        
                        # Check if it's likely an emoji or icon (small SVG)
                        if filename.endswith('.svg') and '1f' in filename:
                            # Likely an emoji, use smaller format
                            new_lines.append(f"![{alt_text}]({relative_path})")
                        else:
                            # Regular image
                            new_lines.append(f"\n![{alt_text}]({relative_path})\n")
                        
                        # Mark this image as used
                        del image_files[original_name]
                        image_found = True
                        break
                
                if not image_found:
                    new_lines.append(line)  # Keep original if no image found
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def create_smart_embedded_version(self, enex_file_path: str, existing_notes_dir: str) -> str:
        """Create a smart version that analyzes content and embeds relevant images"""
        
        print(f"Creating smart embedded version from: {existing_notes_dir}")
        
        notes_path = Path(existing_notes_dir)
        if not notes_path.exists():
            print(f"❌ Notes directory not found: {notes_path}")
            return None
        
        # Parse the original ENEX to get resource mappings
        tree = ET.parse(enex_file_path)
        root = tree.getroot()
        
        # Create mapping of note index to resources
        note_resources = {}
        for note_idx, note_elem in enumerate(root.findall('note'), 1):
            resources = []
            for resource_elem in note_elem.findall('resource'):
                resource_info = self._analyze_resource(resource_elem)
                if resource_info:
                    resources.append(resource_info)
            note_resources[note_idx] = resources
        
        # Create new output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = self.output_base_dir / f"smart_embedded_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy attachments
        import shutil
        attachments_source = notes_path / "attachments"
        if attachments_source.exists():
            new_attachments_dir = output_dir / "attachments"
            shutil.copytree(attachments_source, new_attachments_dir)
        
        # Process each note
        processed_count = 0
        for md_file in notes_path.glob("[0-9]*.md"):
            # Extract note number from filename
            note_num_match = re.match(r'(\d+)_', md_file.name)
            if not note_num_match:
                continue
            
            note_idx = int(note_num_match.group(1))
            
            # Get resources for this note
            resources = note_resources.get(note_idx, [])
            
            # Read the file
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Embed images smartly
            new_content = self._smart_embed_images(content, resources)
            
            # Write to new location
            new_file_path = output_dir / md_file.name
            with open(new_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            processed_count += 1
            if processed_count % 10 == 0:
                print(f"  Processed {processed_count} files...")
        
        # Copy README if exists
        readme_source = notes_path / "README.md"
        if readme_source.exists():
            shutil.copy2(readme_source, output_dir / "README.md")
        
        print(f"\n✅ Successfully created smart embedded version with {processed_count} notes")
        print(f"   Output directory: {output_dir}")
        
        return str(output_dir)
    
    def _analyze_resource(self, resource_elem) -> Dict:
        """Analyze a resource element and extract metadata"""
        
        # Get MIME type
        mime_elem = resource_elem.find('mime')
        mime_type = mime_elem.text if mime_elem is not None else ''
        
        # Get filename
        filename = None
        attrs = resource_elem.find('resource-attributes')
        if attrs is not None:
            filename_elem = attrs.find('file-name')
            if filename_elem is not None:
                filename = filename_elem.text
        
        # Get data for hash
        data_elem = resource_elem.find('data')
        if data_elem is not None and data_elem.text:
            try:
                attachment_data = base64.b64decode(data_elem.text)
                data_hash = hashlib.md5(attachment_data).hexdigest()[:8]
            except:
                data_hash = None
        else:
            data_hash = None
        
        return {
            'mime_type': mime_type,
            'filename': filename,
            'hash': data_hash,
            'is_image': mime_type.startswith('image/') if mime_type else False
        }
    
    def _smart_embed_images(self, content: str, resources: List[Dict]) -> str:
        """Smartly embed images based on resource information"""
        
        # Get image resources
        image_resources = [r for r in resources if r['is_image']]
        
        if not image_resources:
            return content
        
        lines = content.split('\n')
        new_lines = []
        image_index = 0
        
        for line in lines:
            if '[Attachment]' in line and image_index < len(image_resources):
                # Use the next available image
                resource = image_resources[image_index]
                
                # Generate filename (same logic as in extractor)
                if resource['filename']:
                    clean_filename = resource['filename'].replace('\n', '').replace('\r', '').strip()
                    if len(clean_filename) > 50:
                        name_parts = clean_filename.rsplit('.', 1)
                        if len(name_parts) == 2:
                            clean_filename = f"{name_parts[0][:40]}.{name_parts[1]}"
                        else:
                            clean_filename = clean_filename[:50]
                    filename = f"{resource['hash']}_{clean_filename}"
                else:
                    ext = self._get_extension_from_mime(resource['mime_type'])
                    filename = f"{resource['hash']}{ext}"
                
                relative_path = f"attachments/{filename}"
                alt_text = resource['filename'] or 'Image'
                
                # Check if it's likely an emoji/icon
                if (filename.endswith('.svg') and 
                    (len(alt_text) < 20 or '1f' in filename or 'emoji' in filename.lower())):
                    # Inline emoji/icon
                    new_lines.append(f"![{alt_text}]({relative_path})")
                else:
                    # Block image with spacing
                    new_lines.append(f"\n![{alt_text}]({relative_path})\n")
                
                image_index += 1
            else:
                new_lines.append(line)
        
        return '\n'.join(new_lines)
    
    def _get_extension_from_mime(self, mime_type: str) -> str:
        """Get file extension from MIME type"""
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/svg+xml': '.svg',
            'image/webp': '.webp',
        }
        return mime_to_ext.get(mime_type, '.bin')
    
    def _create_index(self, output_dir: Path, note_count: int):
        """Create an index file"""
        index_content = f"# Notes with Embedded Images\n\n"
        index_content += f"Generated: {datetime.now().isoformat()}\n"
        index_content += f"Total notes: {note_count}\n\n"
        index_content += "Images are now embedded directly in the markdown files.\n\n"
        
        # List all note files
        for md_file in sorted(output_dir.glob("[0-9]*.md")):
            title = md_file.stem
            # Clean up the filename for display
            if '_' in title:
                parts = title.split('_', 1)
                if len(parts) > 1:
                    display_title = parts[1].replace('_', ' ')
                else:
                    display_title = title
            else:
                display_title = title
            
            index_content += f"- [{display_title}]({md_file.name})\n"
        
        with open(output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(index_content)


def main():
    if len(sys.argv) < 3:
        print("Usage: python final_image_embedder.py <enex_file> <existing_notes_directory>")
        print("\nThis will create a new version with properly embedded images")
        sys.exit(1)
    
    enex_path = sys.argv[1]
    notes_dir = sys.argv[2]
    
    if not os.path.exists(enex_path):
        print(f"❌ ENEX file not found: {enex_path}")
        sys.exit(1)
    
    if not os.path.exists(notes_dir):
        print(f"❌ Notes directory not found: {notes_dir}")
        sys.exit(1)
    
    embedder = FinalImageEmbedder()
    result = embedder.create_smart_embedded_version(enex_path, notes_dir)
    
    if result:
        print(f"\n🎉 Success! Check out your notes with embedded images at:")
        print(f"   {result}")


if __name__ == "__main__":
    main()