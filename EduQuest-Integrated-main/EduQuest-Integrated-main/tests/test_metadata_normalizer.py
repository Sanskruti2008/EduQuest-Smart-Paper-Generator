from src.utils.metadata_normalizer import MetadataNormalizer


def test_unit_falls_back_when_unit_id_is_null():
    normalized = MetadataNormalizer.normalize_question(
        {
            "question_text": "What is communication?",
            "unit_id": None,
            "unit": "Unit-I",
            "course_outcome": "CO1",
        }
    )

    assert normalized["unit_id"] == "Unit-I"


def test_question_repository_prefers_unit_label_over_foreign_key():
    from paper_generation.repositories.question_repository import QuestionRepository

    normalized = QuestionRepository._normalize_question_record(
        {
            "canonical_id": 1,
            "question_text": "What is communication?",
            "unit_id": 188,
            "unit": "Unit-I",
            "course_outcome": "CO1",
            "marks": 5,
            "rua": "U",
            "difficulty": "Medium",
        }
    )

    assert normalized["unit"] == "Unit-I"