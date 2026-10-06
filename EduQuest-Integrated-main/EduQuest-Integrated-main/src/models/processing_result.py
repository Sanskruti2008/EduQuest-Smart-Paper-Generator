from dataclasses import dataclass, field


@dataclass
class ProcessingResult:

    question_id: str

    question_text: str

    embedding: list = field(
        default_factory=list
    )

    similar_questions: list = field(
        default_factory=list
    )

    similarity_score: float = 0.0

    is_duplicate: bool = False

    canonical_id: str = None

    canonical_question: str = None

    stored_in_chroma: bool = False

    added_to_unique_bank: bool = False

    processing_time: float = 0.0