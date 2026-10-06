from src.utils.metadata_normalizer import (
    MetadataNormalizer
)


class DatasetProcessor:

    def __init__(
        self,
        question_processor
    ):

        self.question_processor = (
            question_processor
        )

    def process(
        self,
        dataset
    ):

        # ==================================================
        # VALIDATE DATASET
        # ==================================================

        if not isinstance(dataset, dict):
            raise ValueError(
                "Dataset must be a dictionary."
            )

        subject = dataset.get("subject")

        if not subject:
            raise ValueError(
                "Dataset is missing required field: 'subject'."
            )

        subject = str(subject).strip()

        if not subject:
            raise ValueError(
                "Dataset subject cannot be empty."
            )

        questions = dataset.get("questions")

        if not isinstance(questions, list):
            raise ValueError(
                "Dataset 'questions' must be a list."
            )

        report = {

            "subject":
                subject,

            "processed":
                0,

            "duplicates":
                0,

            "new_questions":
                0,

            "failed":
                0,

            "results":
                []
        }

        # ==================================================
        # PROCESS QUESTIONS
        # ==================================================

        for index, question in enumerate(
            questions,
            start=1
        ):

            try:

                normalized_question = (
                    MetadataNormalizer
                    .normalize_question(
                        question
                    )
                )

                result = (
                    self.question_processor
                    .process(
                        question=
                            normalized_question,
                        subject=
                            subject
                    )
                )

                report["processed"] += 1

                if result["is_duplicate"]:

                    report["duplicates"] += 1

                else:

                    report["new_questions"] += 1

                report["results"].append(
                    result
                )

            except Exception as e:

                report["failed"] += 1

                raise ValueError(
                    f"Failed to process question "
                    f"{index}: {e}"
                ) from e

        return report