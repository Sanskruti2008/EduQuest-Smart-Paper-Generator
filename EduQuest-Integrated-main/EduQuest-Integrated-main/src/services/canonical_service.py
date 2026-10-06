class CanonicalService:

    def __init__(
        self,
        repository
    ):

        self.repository = repository

    # ==================================================
    # DUPLICATE CHECK
    # ==================================================

    def is_duplicate(
        self,
        distance: float,
        threshold: float = 0.50
    ):

        return distance <= threshold

    # ==================================================
    # CREATE CANONICAL
    # ==================================================

    def create_canonical(
        self,
        question,
        subject,
        **metadata
    ):

        return (
            self.repository
            .add_canonical(
                canonical_question=question,
                subject=subject,
                **metadata
            )
        )

    # ==================================================
    # GET CANONICAL
    # ==================================================

    def get_canonical(
        self,
        canonical_id
    ):

        return (
            self.repository
            .get_by_id(
                canonical_id
            )
        )

    # ==================================================
    # GET ALL CANONICAL QUESTIONS
    # ==================================================

    def get_all_canonicals(self):

        return (
            self.repository
            .get_all()
        )

    # ==================================================
    # COUNT
    # ==================================================

    def count_canonicals(self):

        return (
            self.repository
            .count()
        )