"""Persistence service for successfully generated question papers."""

from datetime import date, datetime, timezone


class PaperPersistenceService:
    """
    Saves a generated paper and its selected-question usage
    into the existing EduQuest database tables.
    """

    def __init__(self, client):
        self.client = client

    def save_generated_paper(
        self,
        blueprint,
        selection,
        generated_by=None,
        blueprint_db_id=None,
    ):
        # --------------------------------------------------
        # 1. Read basic paper information
        # --------------------------------------------------

        paper_info = blueprint.get("paper_information", {})

        subject_name = paper_info.get("subject")
        exam_type = paper_info.get("exam_type", "University")

        if not subject_name:
            raise ValueError("PERSISTENCE_ERROR: Blueprint subject is missing.")

        # --------------------------------------------------
        # 2. Collect selected questions
        # --------------------------------------------------

        selected_questions = []

        for section in selection.get("sections", {}).values():
            selected_questions.extend(section.get("questions", []))

        expected_count = sum(
            int(section["questions_to_generate"])
            for section in blueprint["question_pattern"].values()
        )
        if len(selected_questions) != expected_count:
            raise ValueError(
                "PERSISTENCE_ERROR: Expected "
                f"{expected_count} generated questions, got "
                f"{len(selected_questions)}."
            )

        canonical_ids = [
            question.get("canonical_id")
            for question in selected_questions
        ]
        if any(canonical_id is None for canonical_id in canonical_ids):
            raise ValueError(
                "PERSISTENCE_ERROR: Selected question missing canonical_id."
            )
        if len(canonical_ids) != len(set(canonical_ids)):
            raise ValueError(
                "PERSISTENCE_ERROR: Duplicate canonical_id in selected paper."
            )

        # --------------------------------------------------
        # 3. Validate question IDs
        # --------------------------------------------------

        missing_question_ids = [
            question.get("canonical_id")
            for question in selected_questions
            if question.get("question_id") is None
        ]
        if missing_question_ids:
            raise ValueError(
                "PERSISTENCE_ERROR: No database question_id for canonical_id(s): "
                + ", ".join(map(str, missing_question_ids))
            )

        question_ids = [
            question["question_id"]
            for question in selected_questions
        ]
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(
                "PERSISTENCE_ERROR: Duplicate question_id in selected paper."
            )

        # --------------------------------------------------
        # 4. Resolve subject_id
        # --------------------------------------------------

        subject_query = (
            self.client
            .table("subject")
            .select("subject_id,subject_name")
        )
        subject_code = paper_info.get("subject_code")
        branch = paper_info.get("branch")
        semester = paper_info.get("semester")

        if subject_code and branch and semester is not None:
            subject_response = (
                subject_query
                .eq("subject_code", str(subject_code).strip())
                .eq("branch", str(branch).strip())
                .eq("semester", str(semester).strip())
                .execute()
            )
            if not subject_response.data:
                subject_response = (
                    self.client
                    .table("subject")
                    .select("subject_id,subject_name")
                    .ilike("subject_name", str(subject_name).strip())
                    .eq("branch", str(branch).strip())
                    .eq("semester", str(semester).strip())
                    .execute()
                )
        else:
            subject_response = (
                subject_query
                .ilike("subject_name", str(subject_name).strip())
                .execute()
            )

        if not subject_response.data:
            subject_identity = subject_name
            if subject_code and branch and semester is not None:
                subject_identity = (
                    f"{subject_name} (code {subject_code}, "
                    f"{branch}, semester {semester})"
                )
            raise ValueError(
                f"PERSISTENCE_ERROR: Subject not found: {subject_identity}"
            )
        if len(subject_response.data) > 1:
            raise ValueError(
                "PERSISTENCE_ERROR: Subject identity is ambiguous: "
                f"{subject_name}"
            )

        subject_id = subject_response.data[0]["subject_id"]

        # --------------------------------------------------
        # 5. Validate selected question IDs exist in DB
        # --------------------------------------------------

        question_response = (
            self.client
            .table("question")
            .select("question_id")
            .in_("question_id", question_ids)
            .execute()
        )

        existing_ids = {
            row["question_id"]
            for row in question_response.data
        }

        unresolved_questions = [
            question
            for question in selected_questions
            if question["question_id"] not in existing_ids
        ]
        if unresolved_questions:
            raise ValueError(
                "PERSISTENCE_ERROR: Database question_id resolution failed for "
                "canonical_id(s): "
                + ", ".join(
                    f"{question['canonical_id']} (question_id="
                    f"{question['question_id']})"
                    for question in unresolved_questions
                )
            )

        # --------------------------------------------------
        # 6. Calculate generated paper totals
        # --------------------------------------------------

        total_questions = len(selected_questions)

        total_marks = sum(
            int(question.get("marks", 0))
            for question in selected_questions
        )
        expected_marks = sum(
            int(section["marks_per_question"])
            * int(section["questions_to_generate"])
            for section in blueprint["question_pattern"].values()
        )
        if total_marks != expected_marks:
            raise ValueError(
                "PERSISTENCE_ERROR: Expected "
                f"{expected_marks} generated marks, got {total_marks}."
            )

        generated_at = datetime.now(timezone.utc).isoformat()
        generation_log = {
            "blueprint_id": blueprint_db_id,
            "generated_by": generated_by,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "generated_at": generated_at,
        }
        try:
            persistence_response = self.client.rpc(
                "persist_generated_question_paper",
                {
                    "p_subject_id": subject_id,
                    "p_exam_type": exam_type,
                    "p_exam_year": date.today().year,
                    "p_raw_json": {
                        "blueprint": blueprint,
                        "selection": selection,
                    },
                    "p_question_ids": question_ids,
                    "p_generation_log": generation_log,
                },
            ).execute()
        except Exception as error:
            raise RuntimeError(
                f"PERSISTENCE_ERROR: Atomic paper persistence failed: {error}"
            ) from error

        persistence = persistence_response.data
        if isinstance(persistence, list) and len(persistence) == 1:
            persistence = persistence[0]
        if not isinstance(persistence, dict):
            raise RuntimeError(
                "PERSISTENCE_ERROR: Atomic paper persistence returned no result."
            )

        paper_id = persistence.get("paper_id")
        generation_id = persistence.get("generation_id")
        mapped_questions = persistence.get("mapped_questions")
        usage_records = persistence.get("usage_records")
        generation_log_records = persistence.get("generation_log_records")
        if (
            paper_id is None
            or generation_id is None
            or persistence.get("paper_records") != 1
            or mapped_questions != total_questions
            or usage_records != total_questions
            or generation_log_records != 1
        ):
            raise RuntimeError(
                "PERSISTENCE_ERROR: Atomic paper persistence was incomplete: "
                f"{persistence!r}"
            )

        # --------------------------------------------------
        # 11. Return persistence result
        # --------------------------------------------------

        return {
            "status": "SAVED",
            "paper_id": paper_id,
            "generation_id": generation_id,
            "subject_id": subject_id,
            "total_questions": total_questions,
            "total_marks": total_marks,
            "generated_at": generated_at,
            "paper_records": 1,
            "mapped_questions": mapped_questions,
            "usage_records": usage_records,
            "generation_log_records": generation_log_records,
        }