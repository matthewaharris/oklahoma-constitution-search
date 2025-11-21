#!/usr/bin/env python3
"""
Clear Data Script - Safely backup and remove old data

This script will:
1. Create a final archive of existing data
2. Clear statute_html directory
3. Optionally clear Pinecone indexes
4. Optionally truncate Supabase tables

Safety features:
- Requires --confirm flag
- Creates backup before deletion
- Shows what will be deleted
- Asks for confirmation at each step
"""

import os
import sys
import shutil
from pathlib import Path
from datetime import datetime
import argparse

# Import clients
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    from config_production import SUPABASE_URL, SUPABASE_KEY

def create_final_backup():
    """Create one final backup before clearing"""
    print("\n" + "="*60)
    print("Creating Final Backup")
    print("="*60)

    # Check if archive script exists
    if not Path('archive_raw_data.py').exists():
        print("[WARNING] archive_raw_data.py not found, skipping backup")
        return False

    # Run archive script
    import subprocess
    result = subprocess.run(['python', 'archive_raw_data.py'], capture_output=True, text=True)

    if result.returncode == 0:
        print("[OK] Backup created successfully")
        return True
    else:
        print(f"[ERROR] Backup failed: {result.stderr}")
        return False

def clear_html_directory(dry_run=False):
    """Clear statute_html directory"""
    print("\n" + "="*60)
    print("Clearing HTML Directory")
    print("="*60)

    html_dir = Path('statute_html')

    if not html_dir.exists():
        print("[INFO] statute_html directory doesn't exist")
        return True

    # Count files
    total_files = sum(1 for _ in html_dir.rglob('*') if _.is_file())
    total_dirs = sum(1 for _ in html_dir.rglob('*') if _.is_dir())

    print(f"\nFound:")
    print(f"  - {total_dirs} directories")
    print(f"  - {total_files} files")

    if total_files == 0:
        print("[INFO] Directory is already empty")
        return True

    if dry_run:
        print("\n[DRY RUN] Would delete statute_html directory")
        return True

    # Ask for confirmation
    response = input(f"\nDelete {total_files} files in {total_dirs} directories? (yes/no): ")
    if response.lower() != 'yes':
        print("[CANCELLED] HTML directory not cleared")
        return False

    # Delete directory
    try:
        shutil.rmtree(html_dir)
        html_dir.mkdir()
        print("[OK] HTML directory cleared")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to clear directory: {e}")
        return False

def clear_pinecone_indexes(dry_run=False):
    """Clear or delete Pinecone indexes"""
    print("\n" + "="*60)
    print("Clearing Pinecone Indexes")
    print("="*60)

    try:
        from pinecone import Pinecone
        from vector_database_builder import ConstitutionVectorBuilder

        builder = ConstitutionVectorBuilder()
        if not builder.setup_clients():
            print("[ERROR] Failed to connect to Pinecone")
            return False

        indexes_to_clear = ['oklahoma-constitution', 'oklahoma-statutes']

        for index_name in indexes_to_clear:
            try:
                index = builder.pinecone_client.Index(index_name)
                stats = index.describe_index_stats()

                print(f"\n{index_name}:")
                print(f"  Total vectors: {stats.total_vector_count}")

                if stats.total_vector_count == 0:
                    print(f"  [INFO] Already empty")
                    continue

                if dry_run:
                    print(f"  [DRY RUN] Would delete all vectors")
                    continue

                # Ask for confirmation
                response = input(f"  Delete all {stats.total_vector_count} vectors? (yes/no): ")
                if response.lower() != 'yes':
                    print(f"  [CANCELLED] Keeping {index_name}")
                    continue

                # Delete all vectors by namespace
                if stats.namespaces:
                    for namespace in stats.namespaces.keys():
                        index.delete(delete_all=True, namespace=namespace)
                        print(f"  [OK] Cleared namespace: {namespace}")
                else:
                    index.delete(delete_all=True)
                    print(f"  [OK] Cleared default namespace")

            except Exception as e:
                print(f"  [ERROR] Failed to clear {index_name}: {e}")

        return True

    except Exception as e:
        print(f"[ERROR] Pinecone operations failed: {e}")
        return False

def clear_supabase_tables(dry_run=False):
    """Truncate Supabase tables"""
    print("\n" + "="*60)
    print("Clearing Supabase Tables")
    print("="*60)

    try:
        from supabase import create_client

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Check current data
        result = supabase.table('statutes').select('id', count='exact').execute()
        count = result.count if hasattr(result, 'count') else len(result.data)

        print(f"\nstatutes table:")
        print(f"  Current records: {count}")

        if count == 0:
            print(f"  [INFO] Already empty")
            return True

        if dry_run:
            print(f"  [DRY RUN] Would truncate table")
            return True

        # Ask for confirmation
        response = input(f"  Delete all {count} records? (yes/no): ")
        if response.lower() != 'yes':
            print(f"  [CANCELLED] Keeping Supabase data")
            return False

        # Truncate table
        # Note: Supabase doesn't have direct TRUNCATE, so we delete all
        result = supabase.table('statutes').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"  [OK] Truncated statutes table")

        return True

    except Exception as e:
        print(f"[ERROR] Supabase operations failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Clear all data and prepare for fresh scraping')
    parser.add_argument('--confirm', action='store_true', help='Required to actually perform deletions')
    parser.add_argument('--skip-backup', action='store_true', help='Skip creating backup archive')
    parser.add_argument('--html-only', action='store_true', help='Only clear HTML files')
    parser.add_argument('--databases-only', action='store_true', help='Only clear databases (Supabase + Pinecone)')

    args = parser.parse_args()

    if not args.confirm:
        print("="*60)
        print("DRY RUN MODE - No changes will be made")
        print("="*60)
        print("\nThis script will:")
        print("  1. Create backup archive (unless --skip-backup)")
        print("  2. Clear statute_html directory")
        print("  3. Clear Pinecone indexes (oklahoma-constitution, oklahoma-statutes)")
        print("  4. Truncate Supabase statutes table")
        print("\nTo actually perform these actions, run:")
        print("  python clear_data.py --confirm")
        print("\nOptions:")
        print("  --html-only        Only clear HTML files")
        print("  --databases-only   Only clear databases")
        print("  --skip-backup      Don't create backup first")
        print("="*60)

    print("\n" + "="*60)
    print("Clear Data Script")
    print("="*60)
    print(f"Mode: {'LIVE' if args.confirm else 'DRY RUN'}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)

    # Step 1: Backup
    if not args.skip_backup and not args.databases_only:
        if args.confirm:
            backup_ok = create_final_backup()
            if not backup_ok:
                print("\n[WARNING] Backup failed. Continue anyway?")
                response = input("Type 'yes' to continue: ")
                if response.lower() != 'yes':
                    print("[CANCELLED] Aborting")
                    return
        else:
            print("\n[DRY RUN] Would create backup archive")

    # Step 2: Clear HTML
    if not args.databases_only:
        clear_html_directory(dry_run=not args.confirm)

    # Step 3: Clear Pinecone
    if not args.html_only:
        clear_pinecone_indexes(dry_run=not args.confirm)

    # Step 4: Clear Supabase
    if not args.html_only:
        clear_supabase_tables(dry_run=not args.confirm)

    print("\n" + "="*60)
    if args.confirm:
        print("Data Clearing Complete!")
    else:
        print("DRY RUN Complete - No changes made")
    print("="*60)

    if not args.confirm:
        print("\nTo actually clear data, run:")
        print("  python clear_data.py --confirm")

    print("\nNext steps:")
    print("  1. Wait for IP whitelist from OSCN")
    print("  2. Run: python scrape_constitution.py")
    print("  3. Run: python scrape_all_titles.py")
    print("  4. Run: python process_all.py")
    print("="*60)

if __name__ == "__main__":
    main()
