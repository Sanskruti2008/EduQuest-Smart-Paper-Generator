from src.pipelines.question_ingestion import (
    QuestionIngestionPipeline
)


def test_question_ingestion():

    pipeline = QuestionIngestionPipeline()

    result = (
        pipeline.process_question(
            "Define communication.",
            "Communication Skills"
        )
    )

    assert result["question"] == (
        "Define communication."
    )

    assert result["embedding_length"] == 384

    assert "search_results" in result

    assert "documents" in (
        result["search_results"]
    )

    assert "distances" in (
        result["search_results"]
    )