class VerbExtractionService:

    VERBS = [
        "define",
        "explain",
        "list",
        "state",
        "mention",
        "name",
        "classify",
        "compare",
        "differentiate",
        "describe",
        "draw",
        "apply",
        "calculate",
        "justify",
        "write",
        "identify"
    ]

    @staticmethod
    def extract(question: str):

        question = question.lower().strip()

        if question.startswith("what is meant by"):
            return "define"

        if question.startswith("what is"):
            return "define"

        if question.startswith("what are"):
            return "define"

        if question.startswith("meaning of"):
            return "define"

        for verb in VerbExtractionService.VERBS:

            if question.startswith(verb):
                return verb

        return "unknown"