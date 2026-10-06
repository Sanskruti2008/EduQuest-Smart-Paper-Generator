#!/usr/bin/env python3
"""
Verification script to test if curriculum units are being saved and retrieved correctly.
Run this after uploading curriculum PDFs to verify data integrity.
"""

from database import get_supabase_client

def verify_curriculum_storage():
    """Query database and verify curriculum units are stored correctly."""
    try:
        sb = get_supabase_client()
        
        # Query all subjects with their unit counts
        print("\n" + "="*70)
        print("CURRICULUM VERIFICATION REPORT")
        print("="*70)
        
        subjects = sb.table("subject").select("*").execute()
        if not subjects.data:
            print("\n[!] No subjects found in database")
            return False
        
        print(f"\n[+] Found {len(subjects.data)} subjects")
        
        all_units_found = 0
        
        for subject in subjects.data:
            subject_id = subject["subject_id"]
            subject_name = subject["subject_name"]
            
            # Get units for this subject
            units = sb.table("unit").select("*").eq("subject_id", subject_id).execute()
            unit_count = len(units.data) if units.data else 0
            all_units_found += unit_count
            
            if unit_count > 0:
                print(f"\n    Subject: {subject_name} (ID: {subject_id})")
                print(f"    Units: {unit_count}")
                
                # List each unit and its topics
                for unit in units.data:
                    unit_id = unit["unit_id"]
                    unit_name = unit["unit_name"]
                    
                    topics = sb.table("topic").select("*").eq("unit_id", unit_id).execute()
                    topic_count = len(topics.data) if topics.data else 0
                    
                    print(f"      - {unit_name} (ID: {unit_id}) -> {topic_count} topics")
        
        print(f"\n[+] Total units found: {all_units_found}")
        
        if all_units_found == 0:
            print("\n[!] WARNING: No units found. Curriculum may not have been saved.")
            return False
        
        print("\n[✓] Curriculum verification PASSED")
        print("="*70 + "\n")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_recent_uploads():
    """Show the most recently uploaded curriculums."""
    try:
        sb = get_supabase_client()
        
        print("\nRECENT CURRICULUM UPLOADS:")
        print("-" * 70)
        
        subjects = (
            sb.table("subject")
            .select("subject_id, subject_name, subject_code, branch, semester")
            .order("subject_id", desc=True)
            .limit(10)
            .execute()
        )
        
        if not subjects.data:
            print("  No subjects found")
            return
        
        for subject in subjects.data:
            subject_id = subject["subject_id"]
            subject_name = subject["subject_name"]
            code = subject.get("subject_code", "N/A")
            branch = subject.get("branch", "N/A")
            sem = subject.get("semester", "N/A")
            
            units = sb.table("unit").select("count", count="exact").eq("subject_id", subject_id).execute()
            unit_count = units.count or 0
            
            print(f"\n  ID {subject_id}: {subject_name}")
            print(f"    Code: {code}, Branch: {branch}, Sem: {sem}")
            print(f"    Units saved: {unit_count}")
    
    except Exception as e:
        print(f"[ERROR] Could not retrieve recent uploads: {e}")

if __name__ == "__main__":
    verify_curriculum_storage()
    check_recent_uploads()
