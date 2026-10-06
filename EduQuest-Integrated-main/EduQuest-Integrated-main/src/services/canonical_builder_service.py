import json

from src.services.duplicate_detection_service import (
    DuplicateDetectionService
)


class CanonicalBuilderService:

    def __init__(self):

        self.duplicate_service = (
            DuplicateDetectionService()
        )

    def build(
        self,
        questions
    ):

        canonicals = []

        for question in questions:

            matched = False

            for canonical in canonicals:

                result = (
                    self.duplicate_service
                    .is_duplicate(
                        question,
                        canonical[
                            "canonical_question"
                        ]
                    )
                )

                if result["is_duplicate"]:

                    canonical[
                        "questions"
                    ].append(
                        question
                    )

                    matched = True
                    break

            if not matched:

                canonicals.append(
                    {
                        "canonical_id":
                        f"CAN_{len(canonicals)+1:03}",

                        "canonical_question":
                        question,

                        "questions":
                        [question]
                    }
                )

        return canonicals