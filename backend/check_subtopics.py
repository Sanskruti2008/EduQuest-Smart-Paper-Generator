from database import get_supabase_client


def main():
    sb = get_supabase_client()

    subjects = sb.table("subject").select("subject_id, subject_name").execute()
    subject = next(
        (row for row in (subjects.data or []) if "client side scripting" in row.get("subject_name", "").lower()),
        None,
    )
    if not subject:
        print("Subject 'Client Side Scripting' not found")
        raise SystemExit(1)
    subject_id = subject["subject_id"]
    print(f"Subject: {subject['subject_name']} (id={subject_id})")

    units = sb.table("unit").select("unit_id, unit_name").eq("subject_id", subject_id).execute()
    if not units.data:
        print("No units found for subject")
        raise SystemExit(0)

    # Check whether the current DB has parent_topic_id.
    supports_parent = True
    try:
        sb.table("topic").select("topic_id, parent_topic_id").limit(1).execute()
    except Exception as exc:
        supports_parent = False
        print(f"parent_topic_id unavailable in this DB: {exc}")

    topic_select = "topic_id, topic_name"
    if supports_parent:
        topic_select += ", parent_topic_id"

    for unit in units.data:
        uid = unit["unit_id"]
        uname = unit["unit_name"]
        topics = (
            sb.table("topic")
            .select(topic_select)
            .eq("unit_id", uid)
            .order("topic_id", desc=False)
            .execute()
        )
        print(f"\nUnit: {uname} (id={uid}) -> {len(topics.data) if topics.data else 0} topic rows")
        if not topics.data:
            continue

        for topic in topics.data:
            topic_id = topic["topic_id"]
            topic_name = topic["topic_name"]
            parent_id = topic.get("parent_topic_id") if supports_parent else None

            if parent_id:
                parent = sb.table("topic").select("topic_name").eq("topic_id", parent_id).limit(1).execute()
                parent_name = parent.data[0]["topic_name"] if parent.data else "<missing>"
                print(f"  - {topic_name} (id={topic_id}) parent_id={parent_id} parent_name={parent_name}")
            else:
                print(f"  - {topic_name} (id={topic_id}) parent_id=None")

    print("\nDone.")


if __name__ == "__main__":
    main()
