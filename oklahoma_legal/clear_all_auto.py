#!/usr/bin/env python3
"""
Auto-clear all data without prompts
"""
import os
import shutil
from pathlib import Path

try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    from config_production import SUPABASE_URL, SUPABASE_KEY

def clear_html_directory():
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

    # Delete directory
    try:
        shutil.rmtree(html_dir)
        html_dir.mkdir()
        print(f"[OK] Deleted {total_files} files in {total_dirs} directories")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to clear directory: {e}")
        return False

def clear_pinecone_indexes():
    """Clear Pinecone indexes"""
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

                # Delete all vectors
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

def clear_supabase_tables():
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

        # Delete all records
        result = supabase.table('statutes').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
        print(f"  [OK] Deleted all {count} records")

        return True

    except Exception as e:
        print(f"[ERROR] Supabase operations failed: {e}")
        return False

def main():
    print("="*60)
    print("Auto Clear All Data")
    print("="*60)
    print("\nThis will clear:")
    print("  - HTML files")
    print("  - Pinecone vectors")
    print("  - Supabase records")
    print("="*60)

    # Clear everything
    clear_html_directory()
    clear_pinecone_indexes()
    clear_supabase_tables()

    print("\n" + "="*60)
    print("Data Clearing Complete!")
    print("="*60)

if __name__ == "__main__":
    main()
