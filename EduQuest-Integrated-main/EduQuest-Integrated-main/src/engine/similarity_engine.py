
from pathlib import Path

from src.services.embedding_service import (
    EmbeddingService
)

from src.services.search_service import (
    SearchService
)

from src.services.duplicate_detection_service import (
    DuplicateDetectionService
)

from src.services.chroma_service import (
    ChromaService
)

from src.services.canonical_service import (
    CanonicalService
)

from src.services.canonical_repository import (
    CanonicalRepository
)

from src.services.unique_question_bank_service import (
    UniqueQuestionBankService
)

from src.repositories.supabase_question_repository import (
    SupabaseQuestionRepository
)

from src.processors.question_processor import (
    QuestionProcessor
)

from src.processors.dataset_processor import (
    DatasetProcessor
)


class SimilarityEngine:

    def __init__(
        self,
        db_path=None,
        canonical_file_path=None,
    ):
        package_root = Path(__file__).resolve().parents[2]
        if db_path is None:
            db_path = str(package_root / "chroma_db")
        if canonical_file_path is None:
            canonical_file_path = str(
                package_root / "data" / "canonical_questions.json"
            )

        print(
            "Initializing Similarity Engine..."
        )

        # ==================================================
        # EMBEDDING SERVICE
        # ==================================================

        self.embedding_service = (
            EmbeddingService()
        )

        # ==================================================
        # CHROMA SERVICE
        # ==================================================

        self.chroma_service = (
            ChromaService(
                db_path=db_path
            )
        )

        # ==================================================
        # SEARCH SERVICE
        # ==================================================

        self.search_service = (
            SearchService(
                self.chroma_service
            )
        )

        # ==================================================
        # DUPLICATE DETECTION SERVICE
        # ==================================================

        self.duplicate_service = (
            DuplicateDetectionService(
                embedding_service=
                    self.embedding_service
            )
        )

        # ==================================================
        # CANONICAL REPOSITORY
        # ==================================================

        self.canonical_repository = (
            CanonicalRepository(
                file_path=
                    canonical_file_path
            )
        )

        # ==================================================
        # CANONICAL SERVICE
        # ==================================================

        self.canonical_service = (
            CanonicalService(
                self.canonical_repository
            )
        )

        # ==================================================
        # UNIQUE QUESTION BANK
        # ==================================================

        self.unique_question_bank = (
            UniqueQuestionBankService(
                self.canonical_repository
            )
        )

        # ==================================================
        # SUPABASE REPOSITORY
        # ==================================================

        self.supabase_repository = (
            SupabaseQuestionRepository()
        )

        # ==================================================
        # QUESTION PROCESSOR
        # ==================================================

        self.question_processor = (
            QuestionProcessor(

                embedding_service=
                    self.embedding_service,

                search_service=
                    self.search_service,

                duplicate_service=
                    self.duplicate_service,

                chroma_service=
                    self.chroma_service,

                canonical_service=
                    self.canonical_service,

                supabase_repository=
                    self.supabase_repository
            )
        )

        # ==================================================
        # DATASET PROCESSOR
        # ==================================================

        self.dataset_processor = (
            DatasetProcessor(
                self.question_processor
            )
        )

    # ======================================================
    # PROCESS DATASET
    # ======================================================

    def process_dataset(
        self,
        dataset
    ):

        print()

        print(
            "========== SIMILARITY ENGINE =========="
        )

        report = (
            self.dataset_processor.process(
                dataset
            )
        )

        print()

        print(
            "========== PROCESS COMPLETED =========="
        )

        return report

    # ======================================================
    # GET ALL UNIQUE QUESTIONS
    # ======================================================

    def get_unique_questions(
        self
    ):

        return (
            self.unique_question_bank
            .get_all_unique_questions()
        )

    # ======================================================
    # GET UNIQUE QUESTIONS BY SUBJECT
    # ======================================================

    def get_unique_questions_by_subject(
        self,
        subject
    ):

        return (
            self.unique_question_bank
            .get_by_subject(
                subject
            )
        )

    # ======================================================
    # GET UNIQUE QUESTION COUNT
    # ======================================================

    def get_unique_question_count(
        self
    ):

        return (
            self.unique_question_bank
            .count()
        )

    # ======================================================
    # GET QUESTIONS FOR PAPER GENERATION
    # ======================================================

    def get_questions_for_generation(
        self,
        subject=None,
        unit_id=None,
        marks=None,
        rua=None,
        difficulty=None,
        bloom_level=None,
        course_outcome=None,
        question_type=None
    ):
        """
        Public interface for the Paper Generation Engine.

        Paper Generation must use this method only.

        It must NOT directly access:

        - Supabase
        - ChromaDB
        - EmbeddingService
        - DuplicateDetectionService
        - CanonicalRepository
        - Internal Similarity Engine components

        Parameters are optional so the Paper Generation
        Engine can retrieve questions at different levels
        of specificity.

        Examples:

        1. Get all questions for a subject:

            engine.get_questions_for_generation(
                subject="Communication Skills"
            )

        2. Get questions for a subject and unit:

            engine.get_questions_for_generation(
                subject="Communication Skills",
                unit_id="Unit 2"
            )

        3. Get questions matching paper requirements:

            engine.get_questions_for_generation(
                subject="Communication Skills",
                unit_id="Unit 2",
                marks=5,
                rua="U",
                difficulty="Medium"
            )
        """

        # --------------------------------------------------
        # Build filters dynamically.
        #
        # Only values actually supplied by the caller are
        # forwarded to Supabase.
        #
        # This keeps the public API clean and also preserves
        # compatibility with simple subject-only calls.
        # --------------------------------------------------

        filters = {}

        if subject is not None:
            filters["subject"] = subject

        if unit_id is not None:
            filters["unit_id"] = unit_id

        if marks is not None:
            filters["marks"] = marks

        if rua is not None:
            filters["rua"] = rua

        if difficulty is not None:
            filters["difficulty"] = difficulty

        if bloom_level is not None:
            filters["bloom_level"] = bloom_level

        if course_outcome is not None:
            filters["course_outcome"] = course_outcome

        if question_type is not None:
            filters["question_type"] = question_type

        return (
            self.supabase_repository
            .get_questions_for_generation(
                **filters
            )
        )
