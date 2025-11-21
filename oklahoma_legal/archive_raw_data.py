#!/usr/bin/env python3
"""
Archive raw statute data with manifest and verification

This creates a timestamped archive of raw HTML/JSON data that can be:
- Backed up to cloud storage
- Version controlled
- Used for reprocessing if schema changes
"""

import os
import json
import hashlib
from pathlib import Path
from datetime import datetime
import zipfile
from typing import Dict, List

def calculate_md5(file_path: Path) -> str:
    """Calculate MD5 hash of a file"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def create_manifest(data_dir: Path) -> Dict:
    """Create a manifest of all files with metadata"""
    manifest = {
        'created_at': datetime.now().isoformat(),
        'data_directory': str(data_dir),
        'files': [],
        'statistics': {}
    }

    html_files = list(data_dir.glob('*.html'))
    json_files = list(data_dir.glob('*.meta.json'))

    print(f"\nCreating manifest for {len(html_files)} HTML files...")

    for html_file in html_files:
        cite_id = html_file.stem.replace('cite_', '')
        meta_file = data_dir / f"cite_{cite_id}.meta.json"

        file_info = {
            'cite_id': cite_id,
            'html_file': html_file.name,
            'html_size': html_file.stat().st_size,
            'html_md5': calculate_md5(html_file),
            'html_modified': datetime.fromtimestamp(html_file.stat().st_mtime).isoformat()
        }

        if meta_file.exists():
            file_info['meta_file'] = meta_file.name
            file_info['meta_size'] = meta_file.stat().st_size
            file_info['meta_md5'] = calculate_md5(meta_file)

            # Include original metadata
            with open(meta_file, 'r') as f:
                file_info['download_metadata'] = json.load(f)

        manifest['files'].append(file_info)

    # Add statistics
    total_html_size = sum(f['html_size'] for f in manifest['files'])
    total_meta_size = sum(f.get('meta_size', 0) for f in manifest['files'])

    manifest['statistics'] = {
        'total_statutes': len(html_files),
        'total_files': len(html_files) + len(json_files),
        'total_html_bytes': total_html_size,
        'total_meta_bytes': total_meta_size,
        'total_bytes': total_html_size + total_meta_size,
        'total_mb': round((total_html_size + total_meta_size) / 1024 / 1024, 2)
    }

    return manifest

def create_archive(data_dir: Path, output_dir: Path = None):
    """Create a timestamped archive with manifest"""

    if output_dir is None:
        output_dir = Path('archives')

    output_dir.mkdir(exist_ok=True)

    # Generate archive name with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    title_name = data_dir.name  # e.g., 'title_10'
    archive_name = f"raw_data_{title_name}_{timestamp}"

    print(f"\n{'='*60}")
    print(f"Creating Archive: {archive_name}")
    print(f"{'='*60}")

    # Create manifest
    manifest = create_manifest(data_dir)

    # Save manifest as JSON
    manifest_path = output_dir / f"{archive_name}_manifest.json"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"\n[OK] Manifest created: {manifest_path}")
    print(f"\nStatistics:")
    print(f"  Total statutes: {manifest['statistics']['total_statutes']}")
    print(f"  Total files: {manifest['statistics']['total_files']}")
    print(f"  Total size: {manifest['statistics']['total_mb']} MB")

    # Create ZIP archive
    zip_path = output_dir / f"{archive_name}.zip"
    print(f"\n[...] Creating ZIP archive...")

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add manifest
        zipf.write(manifest_path, f"{archive_name}/manifest.json")

        # Add all HTML and JSON files
        for file_info in manifest['files']:
            html_file = data_dir / file_info['html_file']
            zipf.write(html_file, f"{archive_name}/{file_info['html_file']}")

            if 'meta_file' in file_info:
                meta_file = data_dir / file_info['meta_file']
                zipf.write(meta_file, f"{archive_name}/{file_info['meta_file']}")

    zip_size_mb = round(zip_path.stat().st_size / 1024 / 1024, 2)
    print(f"[OK] ZIP archive created: {zip_path}")
    print(f"     Compressed size: {zip_size_mb} MB")

    # Create README
    readme_path = output_dir / f"{archive_name}_README.txt"
    with open(readme_path, 'w') as f:
        f.write(f"""Oklahoma Statutes Raw Data Archive
{'='*60}

Archive Name: {archive_name}
Created: {manifest['created_at']}
Source: {manifest['data_directory']}

Contents:
- {manifest['statistics']['total_statutes']} statute HTML files
- {manifest['statistics']['total_statutes']} metadata JSON files
- 1 manifest.json file with checksums and metadata

Statistics:
- Total files: {manifest['statistics']['total_files']}
- Uncompressed size: {manifest['statistics']['total_mb']} MB
- Compressed size: {zip_size_mb} MB

Files:
- {archive_name}.zip - Compressed archive of all raw data
- {archive_name}_manifest.json - Detailed file listing with MD5 checksums
- {archive_name}_README.txt - This file

Reprocessing Instructions:
1. Extract the ZIP file
2. Update database schema if needed
3. Run processing script pointing to extracted directory:
   python html_processor.py --input-dir extracted/{archive_name}

Verification:
- Use manifest.json to verify file integrity via MD5 checksums
- Each file's download timestamp and source URL are preserved

Notes:
- This archive contains raw HTML as downloaded from OSCN
- Original download metadata (timestamp, URL, status code) is preserved
- Can be reprocessed with different parsers or schema versions
""")

    print(f"[OK] README created: {readme_path}")

    print(f"\n{'='*60}")
    print(f"Archive Complete!")
    print(f"{'='*60}")
    print(f"\nFiles created:")
    print(f"  1. {zip_path.name} - Compressed archive")
    print(f"  2. {manifest_path.name} - File manifest with checksums")
    print(f"  3. {readme_path.name} - Documentation")
    print(f"\nBackup recommendations:")
    print(f"  - Upload to cloud storage (Google Drive, Dropbox, OneDrive)")
    print(f"  - Keep local backup on external drive")
    print(f"  - Store manifest separately for quick reference")
    print(f"\n{'='*60}")

def verify_archive(manifest_path: Path, data_dir: Path):
    """Verify data integrity against manifest"""

    print(f"\n{'='*60}")
    print(f"Verifying Archive Integrity")
    print(f"{'='*60}")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    print(f"\nManifest created: {manifest['created_at']}")
    print(f"Checking {len(manifest['files'])} files...")

    errors = []
    verified = 0

    for file_info in manifest['files']:
        html_file = data_dir / file_info['html_file']

        if not html_file.exists():
            errors.append(f"Missing: {file_info['html_file']}")
            continue

        # Verify HTML file
        actual_md5 = calculate_md5(html_file)
        if actual_md5 != file_info['html_md5']:
            errors.append(f"Checksum mismatch: {file_info['html_file']}")
        else:
            verified += 1

        # Verify metadata file if exists
        if 'meta_file' in file_info:
            meta_file = data_dir / file_info['meta_file']
            if meta_file.exists():
                actual_md5 = calculate_md5(meta_file)
                if actual_md5 != file_info['meta_md5']:
                    errors.append(f"Checksum mismatch: {file_info['meta_file']}")
                else:
                    verified += 1

    print(f"\n{'='*60}")
    if errors:
        print(f"[WARNING] Verification found {len(errors)} issues:")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  - {error}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
    else:
        print(f"[OK] All files verified successfully!")
        print(f"     {verified} files matched their checksums")
    print(f"{'='*60}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--verify':
        # Verify mode
        if len(sys.argv) < 4:
            print("Usage: python archive_raw_data.py --verify <manifest.json> <data_dir>")
            sys.exit(1)
        verify_archive(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        # Archive mode
        data_dir = Path('statute_html/title_10')

        if not data_dir.exists():
            print(f"[ERROR] Directory not found: {data_dir}")
            sys.exit(1)

        create_archive(data_dir)
