class MetadataNormalizer:

    @staticmethod
    def normalize_question(question):
        if not isinstance(question, dict):
            raise ValueError(
                "Each question must be a dictionary."
            )

        question_text = (
            question.get("question_text")
            or question.get("question")
        )

        if not question_text:
            raise ValueError(
                "Question is missing 'question_text'."
            )

        normalized = dict(question)

        # -----------------------------------------
        # Question text
        # -----------------------------------------

        normalized["question_text"] = (
            str(question_text).strip()
        )

        # -----------------------------------------
        # Difficulty
        # -----------------------------------------

        normalized["difficulty"] = (
            question.get("difficulty")
            or question.get("difficulty_level")
            or "Medium"
        )

        # -----------------------------------------
        # RUA
        # -----------------------------------------

        normalized["rua_level"] = (
            question.get("rua_level")
            or question.get("rua")
            or "U"
        )

        # -----------------------------------------
        # Unit
        # -----------------------------------------

        if not normalized.get("unit_id"):
            normalized["unit_id"] = (
                question.get("unit_id")
                or question.get("unit")
            )

        # -----------------------------------------
        # Bloom level
        # -----------------------------------------

        normalized["bloom_level"] = (
            question.get("bloom_level")
            or question.get("bloom")
            or "Understand"
        )

        # -----------------------------------------
        # Question type
        # -----------------------------------------

        normalized["question_type"] = (
            question.get("question_type")
            or "Short Answer"
        )

        # -----------------------------------------
        # Marks
        # -----------------------------------------

        normalized["marks"] = (
            question.get("marks")
            if question.get("marks") is not None
            else 5
        )

        # -----------------------------------------
        # Course outcome
        # -----------------------------------------

        normalized["course_outcome"] = (
            question.get("course_outcome")
            or question.get("co")
        )

        # -----------------------------------------
        # Question number
        # -----------------------------------------

        normalized["question_number"] = (
            question.get("question_number")
            if question.get("question_number") is not None
            else ""
        )

        # -----------------------------------------
        # Chapter
        # -----------------------------------------

        normalized["chapter"] = (
            question.get("chapter")
            or question.get("unit")
        )

        return normalized