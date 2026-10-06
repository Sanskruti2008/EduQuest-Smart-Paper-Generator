"""Question usage-history support for paper generation."""


class QuestionUsageService:
    """
    Reads question usage history and attaches usage information
    without disturbing the original candidate order.

    Final selection remains the responsibility of SelectionService.
    """

    def __init__(self, client):
        self.client = client

    def get_usage_counts(self, question_ids):
        """Return usage count for each supplied question_id."""

        if not question_ids:
            return {}

        response = (
            self.client
            .table("questionusagehistory")
            .select("question_id")
            .in_("question_id", list(question_ids))
            .execute()
        )

        usage_counts = {
            question_id: 0
            for question_id in question_ids
        }

        for row in response.data:
            question_id = row["question_id"]

            if question_id in usage_counts:
                usage_counts[question_id] += 1

        return usage_counts

    def get_candidate_usage_counts(self, candidates):
        """Return usage counts keyed by each candidate's canonical_id."""
        question_ids = [
            candidate.get("question_id")
            for candidate in candidates
            if candidate.get("question_id") is not None
        ]
        question_usage_counts = self.get_usage_counts(question_ids)
        return {
            candidate["canonical_id"]: question_usage_counts.get(
                candidate.get("question_id"),
                0,
            )
            for candidate in candidates
        }

    def prioritize_candidates(self, candidates, usage_counts=None):
        """
        Attach usage count to every candidate without changing
        the original candidate order.

        SelectionService can use canonical-keyed usage counts when selecting.
        """
        if usage_counts is None:
            usage_counts = self.get_candidate_usage_counts(candidates)

        for candidate in candidates:
            candidate["_usage_count"] = usage_counts.get(
                candidate["canonical_id"],
                0
            )

        return candidates

    def optimize_selection(self, selection, candidates):
        """
        Replace previously-used selected questions with unused
        equivalent candidates whenever possible.

        A replacement must preserve:
        - unit
        - RUA level
        - marks
        - difficulty
        - course outcome

        Therefore the paper's main blueprint constraints remain unchanged.
        """

        selected_ids = {
            question["question_id"]
            for section in selection["sections"].values()
            for question in section["questions"]
        }

        fresh_candidates = [
            candidate
            for candidate in candidates
            if candidate.get("_usage_count", 0) == 0
            and candidate.get("question_id") not in selected_ids
        ]

        replacements = 0

        for section in selection["sections"].values():

            for index, selected in enumerate(section["questions"]):

                if selected.get("_usage_count", 0) == 0:
                    continue

                matches = [
                    candidate
                    for candidate in fresh_candidates
                    if candidate["unit"] == selected["unit"]
                    and candidate["rua"] == selected["rua"]
                    and candidate["marks"] == selected["marks"]
                    and candidate["difficulty"] == selected["difficulty"]
                    and candidate["course_outcome"] == selected["course_outcome"]
                ]

                if not matches:
                    continue

                replacement = matches[0]

                section["questions"][index] = replacement

                selected_ids.discard(selected["question_id"])
                selected_ids.add(replacement["question_id"])

                fresh_candidates.remove(replacement)

                replacements += 1

        return {
            "selection": selection,
            "replacements": replacements,
        }