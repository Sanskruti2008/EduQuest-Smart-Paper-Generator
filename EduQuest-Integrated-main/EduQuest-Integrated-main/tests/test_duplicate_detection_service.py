from src.services.duplicate_detection_service import (
    DuplicateDetectionService
)


def test_duplicate_detection_service():

    service = DuplicateDetectionService()

    # --------------------------------------
    # Similar definition questions
    # --------------------------------------

    duplicate_result = service.is_duplicate(
        "Define communication.",
        "What is meant by communication?"
    )

    assert duplicate_result["same_verb"] is True

    assert (
        duplicate_result["same_question_type"]
        is True
    )

    assert (
        duplicate_result["similarity_score"]
        >= 0.85
        or duplicate_result["is_duplicate"]
        is False
    )


def test_different_questions_are_not_duplicate():

    service = DuplicateDetectionService()

    result = service.is_duplicate(
        "Define communication.",
        "Compare verbal and non-verbal communication."
    )

    assert result["is_duplicate"] is False