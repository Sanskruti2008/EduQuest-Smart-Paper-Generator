"""End-to-end orchestration service for paper generation."""

import logging

from paper_generation.repositories.question_repository import QuestionRepository
from paper_generation.services.candidate_service import CandidateService
from paper_generation.services.question_usage_service import QuestionUsageService
from paper_generation.services.selection_service import SelectionService
from paper_generation.services.paper_persistence_service import PaperPersistenceService


logger = logging.getLogger(__name__)


class PaperGenerationService:
    """Coordinate the complete paper-generation pipeline."""

    def __init__(self, similarity_engine):
        self.engine = similarity_engine
        self.client = similarity_engine.supabase_repository.client

        self.repository = QuestionRepository.from_similarity_engine(
            similarity_engine
        )

        self.candidate_service = CandidateService()
        self.usage_service = QuestionUsageService(self.client)
        self.selection_service = SelectionService()
        self.persistence_service = PaperPersistenceService(self.client)

    def generate(
        self,
        blueprint,
        subject,
        persist=False,
        blueprint_db_id=None,
        generated_by=None,
    ):
        # 1. Retrieve canonical unique questions
        questions = self.repository.get_questions_for_generation(
            subject=subject
        )

        # 2. Build blueprint-compatible candidates
        candidates = self.candidate_service.get_candidates(
            questions,
            blueprint
        )

        # 3. Attach question usage information and map it for selection.
        try:
            usage_counts = self.usage_service.get_candidate_usage_counts(
                candidates
            )
        except Exception:
            logger.warning(
                "Unable to retrieve question usage history; selecting with "
                "zero historical usage counts.",
                exc_info=True,
            )
            usage_counts = {}

        prioritized_candidates = self.usage_service.prioritize_candidates(
            candidates,
            usage_counts=usage_counts,
        )

        # 4. Generate a fast, valid base selection
        selection = (
            self.selection_service.generate_selection(
                prioritized_candidates,
                blueprint,
                usage_counts=usage_counts,
            )
        )

        # 5. Replace reused questions with exact fresh equivalents
        optimization = (
            self.usage_service.optimize_selection(
                selection,
                prioritized_candidates
            )
        )

        selection = optimization["selection"]

        # 6. Validate optimized selection
        self.selection_service.validate_selection(
            selection,
            blueprint
        )

        generated_questions = [
            question
            for section in selection["sections"].values()
            for question in section["questions"]
        ]

        difficulty_validation = (
            self.selection_service.validate_generated_difficulty(
                generated_questions,
                blueprint
            )
        )

        if difficulty_validation["status"] != "VALID":
            raise ValueError(
                "USAGE_OPTIMIZATION_INVALID_DIFFICULTY"
            )

        # 7. Build generation result
        result = {
            "retrieved_questions": len(questions),
            "candidate_questions": len(candidates),
            "selection": selection,
            "usage_optimization": {
                "replacements": optimization["replacements"],
            },
        }

        # 8. Persist only when explicitly requested
        if persist:
            result["persistence"] = (
                self.persistence_service.save_generated_paper(
                    blueprint,
                    selection,
                    generated_by=generated_by,
                    blueprint_db_id=blueprint_db_id,
                )
            )

        # 9. Return complete generation result
        return result