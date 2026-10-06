from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Question:

    question_id: Optional[str] = None

    canonical_id: Optional[str] = None

    text: str = ""

    subject: str = ""

    department: str = ""

    semester: int = 0

    unit: str = ""

    concept: str = ""

    marks: int = 0

    difficulty: str = ""

    rua: str = ""

    intent: str = ""

    embedding: List[float] = field(
        default_factory=list
    )

    similar_questions: List[str] = field(
        default_factory=list
    )