from src.services.canonical_repository import (
    CanonicalRepository
)


class UniqueQuestionBankService:

    def __init__(
        self,
        repository=None
    ):

        if repository is None:
            repository = CanonicalRepository()

        self.repository = repository

    # ==================================================
    # FORMAT CANONICAL QUESTION
    # ==================================================

    def _format_question(self, item):

        canonical_question = item.get(
            "canonical_question"
        )

        return {
            "canonical_id":
                item.get("canonical_id"),

            "canonical_question":
                canonical_question,

            # Compatibility alias
            "question":
                canonical_question,

            "subject":
                item.get("subject"),

            "branch":
                item.get("branch"),

            "semester":
                item.get("semester"),

            "question_type":
                item.get("question_type"),

            "verb":
                item.get("verb")
        }

    # ==================================================
    # GET ALL UNIQUE QUESTIONS
    # ==================================================

    def get_all_unique_questions(self):

        canonicals = (
            self.repository.get_all()
        )

        return [
            self._format_question(item)
            for item in canonicals
        ]

    # ==================================================
    # GET BY SUBJECT
    # ==================================================

    def get_by_subject(
        self,
        subject
    ):

        canonicals = (
            self.repository.get_all()
        )

        results = []

        for item in canonicals:

            if (
                item.get("subject")
                == subject
            ):

                results.append(
                    self._format_question(item)
                )

        return results

    # ==================================================
    # COUNT
    # ==================================================

    def count(self):

        return (
            self.repository.count()
        )

    # ==================================================
    # CLEAR
    # ==================================================

    def clear(self):

        self.repository.clear()