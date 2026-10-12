"""Public entry point for the EduQuest Paper Generation Engine."""

from pathlib import Path

from src.engine.similarity_engine import SimilarityEngine
from paper_generation.services.paper_generation_service import (
    PaperGenerationService,
)


def generate_question_paper(
    blueprint,
    subject,
    persist=False,
    output_path=None,
    blueprint_db_id=None,
    generated_by=None,
    persistence_client=None,
):
    """
    Generate a validated question paper from an approved blueprint.

    This is the public integration interface for the
    EduQuest Paper Generation Engine.

    Returns:
        Complete generation result including the validated
        selection, usage optimization information, optional
        persistence result, and formatter-ready output.
    """

    engine = SimilarityEngine()
    service = PaperGenerationService(
        engine,
        persistence_client=persistence_client,
    )

    result = service.generate(
        blueprint=blueprint,
        subject=subject,
        persist=persist,
        blueprint_db_id=blueprint_db_id,
        generated_by=generated_by,
    )

    formatter_output = service.selection_service.export_selected_questions(
        result["selection"],
        blueprint,
        output_path,
    )

    result["formatter_output"] = formatter_output

    if output_path is not None:
        result["formatter_output_path"] = str(Path(output_path))

    return result