from src.services.canonical_assignment_service import (
    CanonicalAssignmentService
)


def test_canonical_assignment():

    service = CanonicalAssignmentService()

    result = service.assign(
        question_text="What is communication?",
        subject="Communication Skills"
    )

    assert "is_duplicate" in result
    assert "matched_question" in result
    assert "distance" in result
    assert "canonical_id" in result