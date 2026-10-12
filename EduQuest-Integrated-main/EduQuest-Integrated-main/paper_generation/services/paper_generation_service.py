"""End-to-end orchestration service for paper generation."""

import copy
import logging
import random

from paper_generation.repositories.question_repository import QuestionRepository
from paper_generation.services.candidate_service import CandidateService
from paper_generation.services.question_usage_service import QuestionUsageService
from paper_generation.services.selection_service import SelectionService
from paper_generation.services.paper_persistence_service import PaperPersistenceService


logger = logging.getLogger(__name__)


class PaperGenerationService:
    """Coordinate the complete paper-generation pipeline."""

    def __init__(self, similarity_engine, persistence_client=None):
        self.engine = similarity_engine
        self.client = similarity_engine.supabase_repository.client

        self.repository = QuestionRepository.from_similarity_engine(
            similarity_engine
        )

        self.candidate_service = CandidateService()
        self.history_client = persistence_client or self.client
        self.usage_service = QuestionUsageService(self.history_client)
        self.selection_service = SelectionService()
        self.persistence_service = PaperPersistenceService(persistence_client)

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
            usage_counts = self.usage_service.get_candidate_usage_metadata(
                candidates
            )
        except Exception:
            logger.warning(
                "Unable to retrieve question usage history; selecting with "
                "zero historical usage counts.",
                exc_info=True,
            )
            usage_counts = {}

        previous_signatures = []
        history_status = "UNAVAILABLE"
        if persist:
            try:
                previous_signatures = (
                    self.usage_service.get_previous_paper_signatures(blueprint)
                )
                history_status = "AVAILABLE"
            except Exception:
                logger.warning(
                    "Unable to retrieve previous paper signatures; variation "
                    "will rely on usage history only.",
                    exc_info=True,
                )

        prioritized_candidates = self.usage_service.prioritize_candidates(
            candidates,
            usage_counts=usage_counts,
        )

        # 4. Generate a valid selection that avoids prior canonical combinations.
        selection = None
        optimization = None
        variation_status = "NO_PRIOR_PAPERS"
        fallback = None
        prior_combinations = {
            signature["combination"]
            for signature in previous_signatures
        }
        random_source = random.SystemRandom()
        attempts = max(8, min(24, len(prior_combinations) + 8))
        exclusion_failed = False
        for _ in range(attempts if previous_signatures else 1):
            seed = random_source.randrange(0, 2**63)
            try:
                candidate_selection = self.selection_service.generate_selection(
                    prioritized_candidates,
                    blueprint,
                    usage_counts=usage_counts,
                    seed=seed,
                    excluded_combinations=prior_combinations,
                )
            except ValueError as error:
                if not previous_signatures or not str(error).startswith(
                    "UNSATISFIABLE_SELECTION:"
                ):
                    raise
                exclusion_failed = True
                candidate_selection = self.selection_service.generate_selection(
                    prioritized_candidates,
                    blueprint,
                    usage_counts=usage_counts,
                    seed=seed,
                )
            candidate_optimization = self.usage_service.optimize_selection(
                candidate_selection,
                prioritized_candidates,
                rng=random.Random(seed),
            )
            candidate_selection = candidate_optimization["selection"]
            self.selection_service.validate_selection(candidate_selection, blueprint)
            generated_questions = [
                question
                for section in candidate_selection["sections"].values()
                for question in section["questions"]
            ]
            difficulty_validation = self.selection_service.validate_generated_difficulty(
                generated_questions,
                blueprint,
            )
            if difficulty_validation["status"] != "VALID":
                raise ValueError("USAGE_OPTIMIZATION_INVALID_DIFFICULTY")

            signature = self.usage_service.paper_signature(candidate_selection)
            if fallback is None:
                fallback = (candidate_selection, candidate_optimization)
            if exclusion_failed:
                break
            if not previous_signatures or signature["combination"] not in prior_combinations:
                selection = candidate_selection
                optimization = candidate_optimization
                variation_status = (
                    "DIFFERENT_COMBINATION"
                    if previous_signatures
                    else "NO_PRIOR_PAPERS"
                )
                break

        if selection is None and fallback is not None:
            fallback_selection, fallback_optimization = fallback
            prior_sequences = {
                signature["sequence"]
                for signature in previous_signatures
                if signature["combination"] == (
                    self.usage_service.paper_signature(fallback_selection)["combination"]
                )
            }
            for attempt in range(24):
                candidate_selection = self.selection_service.vary_question_order(
                    copy.deepcopy(fallback_selection),
                    seed=random_source.randrange(0, 2**63),
                )
                self.selection_service.validate_selection(candidate_selection, blueprint)
                signature = self.usage_service.paper_signature(candidate_selection)
                if signature["sequence"] not in prior_sequences:
                    selection = candidate_selection
                    optimization = fallback_optimization
                    variation_status = "DIFFERENT_SEQUENCE"
                    break
            if selection is None:
                selection = fallback_selection
                optimization = fallback_optimization
                variation_status = "EXHAUSTED"

        # 7. Build generation result
        result = {
            "retrieved_questions": len(questions),
            "candidate_questions": len(candidates),
            "selection": selection,
            "usage_optimization": {
                "replacements": optimization["replacements"],
            },
            "variation": {
                "status": variation_status,
                "history_status": history_status,
                "previous_papers": len(previous_signatures),
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