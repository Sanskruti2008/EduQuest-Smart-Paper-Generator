"""Repository access and external-record normalization for paper generation."""

from paper_generation.data.sample_questions import sample_questions

# Production source: QuestionRepository -> Supabase Unique Question Bank.
# The sample_questions import is retained as the development mock source.

class QuestionRepository:

    REQUIRED_FIELDS = (
        "canonical_id",
        "question_text",
        "unit",
        "marks",
        "rua",
        "difficulty",
        "course_outcome",
    )

    def __init__(self, source=None):
        # Development source; production will provide Supabase retrieval records.
        self._source = sample_questions if source is None else source

    @classmethod
    def from_similarity_engine(cls, engine):
        """Create a repository backed only by the SimilarityEngine contract."""
        return cls(SimilarityEngineSource(engine))

    def get_questions_for_generation(
        self,
        subject_id=None,
        subject=None,
        unit=None,
        marks=None,
        rua=None,
        difficulty=None,
        unit_id=None,
        bloom_level=None,
        course_outcome=None,
        question_type=None,
        limit=None,
    ):
        """Return normalized questions, optionally narrowed by retrieval filters."""
        retrieval_filters = {
            "subject": subject,
            "unit_id": unit_id,
            "marks": marks,
            "rua": rua,
            "difficulty": difficulty,
            "bloom_level": bloom_level,
            "course_outcome": course_outcome,
            "question_type": question_type,
        }
        if isinstance(self._source, SimilarityEngineSource):
            records = self._source.get_questions_for_generation(
                **{key: value for key, value in retrieval_filters.items() if value is not None}
            )
        else:
            records = self._source

        questions = [self._normalize_question_record(record) for record in records]
        ids = [question["canonical_id"] for question in questions]
        if len(ids) != len(set(ids)):
            raise ValueError("DUPLICATE_CANONICAL_ID: retrieved questions are not unique")
        if subject_id is not None:
            questions = [
                question for question in questions
                if question.get("subject_id") == subject_id
            ]
        if subject is not None and not isinstance(
            self._source,
            SimilarityEngineSource
             ):
            questions = [
            question
            for question in questions
            if question.get("subject") == subject
    ]
        if unit is not None:
            normalized_unit = self._normalize_unit(unit)
            questions = [
                question for question in questions
                if question["unit"] == normalized_unit
            ]
        for field, value in (
            ("marks", marks),
            ("rua", rua),
            ("difficulty", difficulty),
            ("bloom_level", bloom_level),
            ("course_outcome", course_outcome),
            ("question_type", question_type),
        ):
            if value is not None:
                questions = [question for question in questions if question[field] == value]
        return questions if limit is None else questions[:limit]

    @classmethod
    def _normalize_question_record(cls, record):
        """Map retrieval-interface fields into the internal selection contract."""
        normalized = dict(record)
        for wording_field in ("canonical_question", "question_text", "question"):
            if normalized.get(wording_field):
                normalized["question_text"] = normalized[wording_field]
                break
        if normalized.get("course_outcome") is None and "co" in normalized:
            normalized["course_outcome"] = normalized["co"]
        if normalized.get("unit"):
            normalized["unit"] = cls._normalize_unit(normalized["unit"])
        elif "unit_id" in normalized:
            normalized["unit"] = cls._normalize_unit(normalized["unit_id"])

        missing = [
            field for field in cls.REQUIRED_FIELDS
            if field not in normalized or normalized[field] is None or normalized[field] == ""
        ]
        if missing:
            identifier = record.get("canonical_id", "<unknown>")
            raise ValueError(
                f"INVALID_QUESTION_RECORD: {identifier} missing {', '.join(missing)}"
            )
        return normalized

    @staticmethod
    def _normalize_unit(unit):
        if isinstance(unit, int) and not isinstance(unit, bool):
            if unit < 1:
                raise ValueError(f"INVALID_QUESTION_RECORD: invalid unit {unit}")
            return f"Unit-{QuestionRepository._integer_to_roman(unit)}"

        if isinstance(unit, str):
            value = unit.strip()

            if value.lower().startswith("unit "):
                number = value[5:].strip()
                if number.isdigit():
                    return f"Unit-{QuestionRepository._integer_to_roman(int(number))}"

            return value

        return unit
    @staticmethod
    def _integer_to_roman(number):
        """Convert a positive integer to its Roman numeral representation."""
        roman = ""
        values = ((1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
                  (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
                  (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))
        remaining = number
        for value, symbol in values:
            count, remaining = divmod(remaining, value)
            roman += symbol * count
        return roman


class SimilarityEngineSource:
    """Adapter for the public SimilarityEngine retrieval interface."""

    def __init__(self, engine):
        self._engine = engine

    def get_questions_for_generation(self, **filters):
        return self._engine.get_questions_for_generation(**filters)