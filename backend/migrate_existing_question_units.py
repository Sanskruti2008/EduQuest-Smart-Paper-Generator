"""Map existing CO1-CO5 questions to subject-scoped Unit 1-5 rows."""
import os
import re

from dotenv import load_dotenv
from supabase import create_client


CO_PATTERN = re.compile(r"^CO\s*([1-5])$", re.IGNORECASE)


def main() -> None:
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"), override=True)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY/SUPABASE_KEY are required")

    sb = create_client(url, key)
    questions = (
        sb.table("question")
        .select("question_id, subject_id, course_outcome, unit_id")
        .not_.is_("course_outcome", "null")
        .execute()
        .data
        or []
    )

    unit_cache = {}
    updated = 0
    created = 0
    skipped = 0

    for question in questions:
        match = CO_PATTERN.fullmatch(str(question.get("course_outcome") or "").strip())
        if not match or not question.get("subject_id"):
            skipped += 1
            continue

        unit_number = int(match.group(1))
        subject_id = question["subject_id"]
        cache_key = (subject_id, unit_number)
        unit_id = unit_cache.get(cache_key)

        if unit_id is None:
            unit_name = f"Unit {unit_number}"
            existing = (
                sb.table("unit")
                .select("unit_id")
                .eq("subject_id", subject_id)
                .ilike("unit_name", unit_name)
                .limit(1)
                .execute()
                .data
                or []
            )
            if existing:
                unit_id = existing[0]["unit_id"]
            else:
                unit_id = (
                    sb.table("unit")
                    .insert({"unit_name": unit_name, "subject_id": subject_id})
                    .execute()
                    .data[0]["unit_id"]
                )
                created += 1
            unit_cache[cache_key] = unit_id

        if question.get("unit_id") != unit_id:
            sb.table("question").update({"unit_id": unit_id}).eq("question_id", question["question_id"]).execute()
            updated += 1

    print(f"Existing questions scanned: {len(questions)}")
    print(f"Units created: {created}")
    print(f"Questions updated: {updated}")
    print(f"Questions skipped: {skipped}")


if __name__ == "__main__":
    main()