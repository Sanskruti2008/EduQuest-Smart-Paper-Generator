from src.engine.similarity_engine import (
    SimilarityEngine
)


def test_unique_question_bank():

    engine = SimilarityEngine(
        db_path="./test_chroma_db",
        canonical_file_path=(
            "data/test_canonical_questions.json"
        )
    )

    questions = (
        engine.get_unique_questions()
    )

    assert isinstance(
        questions,
        list
    )

    for question in questions:

        assert "canonical_id" in question

        assert "canonical_question" in question

        assert "subject" in question