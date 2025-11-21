#!/usr/bin/env python3
"""
Move all files and directories into oklahoma_legal subdirectory
"""
import os
import shutil
import subprocess

# Get current directory
current_dir = os.getcwd()
target_dir = os.path.join(current_dir, "oklahoma_legal")

# Ensure target directory exists
os.makedirs(target_dir, exist_ok=True)

# Items to exclude from moving
exclude = {'.git', '.claude', 'oklahoma_legal', 'move_to_subdirectory.py'}

# Get all items in current directory
all_items = os.listdir(current_dir)

moved_count = 0
for item in all_items:
    if item in exclude:
        continue

    source_path = os.path.join(current_dir, item)
    dest_path = os.path.join(target_dir, item)

    try:
        # Try git mv first (preserves history for tracked files)
        result = subprocess.run(
            ['git', 'mv', item, f'oklahoma_legal/{item}'],
            capture_output=True,
            text=True,
            cwd=current_dir
        )

        if result.returncode == 0:
            print(f"[OK] git mv: {item}")
            moved_count += 1
        else:
            # If git mv fails, use regular move
            shutil.move(source_path, dest_path)
            print(f"[OK] mv: {item}")
            moved_count += 1

    except Exception as e:
        print(f"[FAIL] Failed to move {item}: {e}")

print(f"\nMoved {moved_count} items to oklahoma_legal/")
