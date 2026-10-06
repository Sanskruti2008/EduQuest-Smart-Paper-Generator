from src.engine.similarity_engine import SimilarityEngine
from paper_generation.repositories.question_repository import QuestionRepository


def test_paper_generation_live_retrieval():
    engine = SimilarityEngine()
    repository = QuestionRepository.from_similarity_engine(engine)

    questions = repository.get_questions_for_generation(
        subject="Advanced Java"
    )

    assert isinstance(questions, list)

    canonical_ids = [question["canonical_id"] for question in questions]
    assert len(canonical_ids) == len(set(canonical_ids))

    required_fields = (
        "canonical_id",
        "question_text",
        "marks",
        "rua",
        "difficulty",
        "unit",
        "course_outcome",
    )

    for question in questions:
        for field in required_fields:
            assert field in question

    metadata_fields = (
        ("unit", "unit"),
        ("course_outcome", "course_outcome"),
        ("marks", "marks"),
        ("rua", "rua"),
        ("difficulty", "difficulty"),
    )

    print(f"TOTAL RETURNED = {len(questions)}")
    for field, output_name in metadata_fields:
        populated = sum(
            question.get(field) is not None
            and question.get(field) != ""
            for question in questions
        )
        print(f"{output_name}: {populated}/{len(questions)} populated")

    for question in questions[:3]:
        print(
            {
                "canonical_id": question["canonical_id"],
                "question_text": question["question_text"],
                "unit": question.get("unit"),
                "course_outcome": question.get("course_outcome"),
                "marks": question.get("marks"),
                "rua": question.get("rua"),
                "difficulty": question.get("difficulty"),
            }
        )