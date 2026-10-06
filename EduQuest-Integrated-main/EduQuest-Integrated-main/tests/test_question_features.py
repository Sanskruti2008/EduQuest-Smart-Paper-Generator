from src.services.question_feature_service import (
    QuestionFeatureService
)


def test_question_feature_extraction():

    service = QuestionFeatureService()

    result = service.extract(
        "Define communication."
    )

    assert "normalized_text" in result
    assert "verb" in result
    assert "question_type" in result

    assert result["normalized_text"] == (
        "define communication"
    )

    assert result["question_type"] == (
        "definition"
    )