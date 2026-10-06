"""
Seed script: Insert 'Communication Skills (CMS)' subject + 5 units + topics
into the Supabase database so it is available for every branch.
Run once: python backend/seed_cms_subject.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import get_supabase_client

CMS_UNITS = [
    {
        "name": "Unit I – Introduction to Communication",
        "topics": [
            "Concept and Importance of Communication",
            "Process and Elements of Communication",
            "Types of Communication",
            "Barriers to Communication",
            "Overcoming Communication Barriers",
        ],
    },
    {
        "name": "Unit II – Reading and Writing Skills",
        "topics": [
            "Reading Comprehension Strategies",
            "Skimming and Scanning",
            "Paragraph Writing",
            "Essay Writing",
            "Vocabulary Building",
        ],
    },
    {
        "name": "Unit III – Speaking and Listening Skills",
        "topics": [
            "Active Listening Techniques",
            "Public Speaking",
            "Group Discussion",
            "Presentation Skills",
            "Interview Skills",
        ],
    },
    {
        "name": "Unit IV – Business Communication",
        "topics": [
            "Formal vs Informal Communication",
            "Business Letter Writing",
            "Email Etiquette",
            "Report Writing",
            "Meeting and Minutes",
        ],
    },
    {
        "name": "Unit V – Technical Communication",
        "topics": [
            "Technical Report Writing",
            "Technical Proposal",
            "User Manuals and Documentation",
            "Visual Communication",
            "Research Paper Writing",
        ],
    },
]

def upsert_subject(sb, name: str) -> int:
    # Keep seed rows compatible with upload-created subject identity fields.
    r = (sb.table("subject").select("subject_id")
         .ilike("subject_name", name).eq("subject_code", "")
         .eq("branch", "").eq("semester", "").limit(1).execute())
    if r.data:
        sid = r.data[0]["subject_id"]
        print(f"  Subject already exists (id={sid}): {name}")
    else:
        ins = sb.table("subject").insert({
            "subject_name": name,
            "subject_code": "",
            "branch": "",
            "semester": "",
        }).execute()
        sid = ins.data[0]["subject_id"]
        print(f"  Created subject (id={sid}): {name}")
    return sid

def upsert_unit(sb, subject_id: int, unit_name: str) -> int:
    r = sb.table("unit").select("unit_id") \
        .eq("subject_id", subject_id).eq("unit_name", unit_name).limit(1).execute()
    if r.data:
        uid = r.data[0]["unit_id"]
        print(f"    Unit already exists (id={uid}): {unit_name}")
    else:
        ins = sb.table("unit").insert({"unit_name": unit_name, "subject_id": subject_id}).execute()
        uid = ins.data[0]["unit_id"]
        print(f"    Created unit (id={uid}): {unit_name}")
    return uid

def upsert_topic(sb, unit_id: int, topic_name: str) -> None:
    r = sb.table("topic").select("topic_id") \
        .eq("unit_id", unit_id).eq("topic_name", topic_name).limit(1).execute()
    if r.data:
        print(f"      Topic exists: {topic_name}")
    else:
        sb.table("topic").insert({"topic_name": topic_name, "unit_id": unit_id}).execute()
        print(f"      Created topic: {topic_name}")

def main():
    print("Connecting to Supabase...")
    sb = get_supabase_client()
    print("Connected.\n")

    subject_name = "Communication Skills (CMS)"
    print(f"Seeding subject: {subject_name}")
    subject_id = upsert_subject(sb, subject_name)

    for unit in CMS_UNITS:
        unit_id = upsert_unit(sb, subject_id, unit["name"])
        for topic in unit["topics"]:
            upsert_topic(sb, unit_id, topic)

    print("\nDone. Communication Skills (CMS) is now in the database for all branches.")

if __name__ == "__main__":
    main()
