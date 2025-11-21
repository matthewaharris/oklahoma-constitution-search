#!/usr/bin/env python3
"""
Check case law and AG opinion data in Supabase
"""

import os
import sys
from supabase import create_client

# Load credentials
try:
    from config import SUPABASE_URL, SUPABASE_KEY
except ImportError:
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: Missing Supabase credentials")
    sys.exit(1)

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("=" * 60)
print("CASE LAW & AG OPINION DATA CHECK")
print("=" * 60)

# Check oklahoma_cases table
try:
    cases_response = supabase.table('oklahoma_cases').select('*', count='exact').execute()
    cases_count = cases_response.count
    print(f"\nOklahoma Cases: {cases_count} records")

    # Count by court type
    for court_type in ['supreme_court', 'criminal_appeals', 'civil_appeals']:
        court_response = supabase.table('oklahoma_cases').select('*', count='exact').eq('court_type', court_type).execute()
        print(f"  - {court_type}: {court_response.count}")

    # Sample a few cases
    if cases_count > 0:
        sample_cases = supabase.table('oklahoma_cases').select('citation, case_title, decision_date').limit(3).execute()
        print(f"\nSample cases:")
        for case in sample_cases.data:
            print(f"  - {case['citation']}: {case['case_title'][:60]}... ({case['decision_date']})")

except Exception as e:
    print(f"ERROR checking cases: {e}")

# Check attorney_general_opinions table
try:
    ag_response = supabase.table('attorney_general_opinions').select('*', count='exact').execute()
    ag_count = ag_response.count
    print(f"\nAttorney General Opinions: {ag_count} records")

    # Count by year
    for year in [2020, 2021, 2022, 2023, 2024, 2025]:
        year_response = supabase.table('attorney_general_opinions').select('*', count='exact').eq('opinion_year', year).execute()
        if year_response.count > 0:
            print(f"  - {year}: {year_response.count}")

    # Sample a few AG opinions
    if ag_count > 0:
        sample_ag = supabase.table('attorney_general_opinions').select('citation, requestor_name, opinion_date').limit(3).execute()
        print(f"\nSample AG opinions:")
        for ag in sample_ag.data:
            print(f"  - {ag['citation']}: {ag['requestor_name']} ({ag['opinion_date']})")

except Exception as e:
    print(f"ERROR checking AG opinions: {e}")

print("\n" + "=" * 60)
print(f"TOTAL DOCUMENTS TO EMBED: {cases_count + ag_count}")
print("=" * 60)
