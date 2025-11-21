import os
from pathlib import Path

print("Searching for HTML files...")
for root, dirs, files in os.walk('.'):
    # Skip .git and other version control
    if '.git' in root or 'node_modules' in root:
        continue

    html_count = len([f for f in files if f.endswith('.html')])
    if html_count > 0:
        rel_path = os.path.relpath(root, '.')
        print(f'{rel_path}: {html_count} HTML files')
