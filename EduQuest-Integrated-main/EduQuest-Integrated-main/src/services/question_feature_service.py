import re

from src.services.verb_extraction_service import (
    VerbExtractionService
)


class QuestionFeatureService:

    DEFINITION_WORDS = {
        "what is",
        "what are",
        "define",
        "definition of",
        "meaning of"
    }

    LIST_WORDS = {
        "list",
        "enumerate",
        "name",
        "mention",
        "state"
    }

    EXPLANATION_WORDS = {
        "explain",
        "describe",
        "discuss",
        "elaborate"
    }

    COMPARISON_WORDS = {
        "compare",
        "differentiate",
        "difference between",
        "distinguish"
    }

    ADVANTAGE_WORDS = {
        "advantage",
        "advantages",
        "benefit",
        "benefits"
    }

    DISADVANTAGE_WORDS = {
        "disadvantage",
        "disadvantages",
        "limitation",
        "limitations"
    }

    def extract(
        self,
        question_text
    ):

        text = (
            question_text
            .strip()
            .lower()
        )

        normalized_text = (
            self._normalize(text)
        )

        verb = (
            VerbExtractionService.extract(
                question_text
            )
        )

        question_type = (
            self._detect_question_type(
                text
            )
        )

        return {

            "normalized_text":
                normalized_text,

            "verb":
                verb,

            "question_type":
                question_type
        }

    def _normalize(
        self,
        text
    ):

        text = re.sub(
            r"[^\w\s]",
            " ",
            text
        )

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    def _detect_question_type(
        self,
        text
    ):

        for phrase in self.DEFINITION_WORDS:

            if phrase in text:

                return "definition"

        for phrase in self.LIST_WORDS:

            if phrase in text:

                return "list"

        for phrase in self.EXPLANATION_WORDS:

            if phrase in text:

                return "explanation"

        for phrase in self.COMPARISON_WORDS:

            if phrase in text:

                return "comparison"

        for phrase in self.ADVANTAGE_WORDS:

            if phrase in text:

                return "advantages"

        for phrase in self.DISADVANTAGE_WORDS:

            if phrase in text:

                return "disadvantages"

        return "general"