"""Question usage-history and generated-paper variation support."""

import json


class QuestionUsageService:
    """Read usage history and preserve variation metadata for selection."""

    def __init__(self, client):
        self.client = client

    def get_usage_counts(self, question_ids):
        """Return usage count for each supplied question_id."""

        metadata = self.get_usage_metadata(question_ids)
        return {
            question_id: record["usage_count"]
            for question_id, record in metadata.items()
        }

    def get_usage_metadata(self, question_ids):
        """Return usage counts and latest generated-paper timestamps."""

        if not question_ids:
            return {}

        response = (
            self.client
            .table("questionusagehistory")
            .select("question_id,paper_id")
            .in_("question_id", list(question_ids))
            .execute()
        )

        metadata = {
            question_id: {
                "usage_count": 0,
                "last_used_at": None,
            }
            for question_id in question_ids
        }
        usage_rows = response.data or []
        paper_ids = {
            row.get("paper_id")
            for row in usage_rows
            if row.get("paper_id") is not None
        }
        generated_at_by_paper = {}
        if paper_ids:
            log_response = (
                self.client
                .table("papergenerationlog")
                .select("paper_id,generated_at")
                .in_("paper_id", list(paper_ids))
                .execute()
            )
            generated_at_by_paper = {
                row.get("paper_id"): row.get("generated_at")
                for row in (log_response.data or [])
                if row.get("paper_id") is not None
            }

        for row in usage_rows:
            question_id = row.get("question_id")
            if question_id not in metadata:
                continue
            record = metadata[question_id]
            record["usage_count"] += 1
            generated_at = generated_at_by_paper.get(row.get("paper_id"))
            if generated_at is not None and (
                record["last_used_at"] is None
                or str(generated_at) > str(record["last_used_at"])
            ):
                record["last_used_at"] = generated_at

        return metadata

    def get_candidate_usage_counts(self, candidates):
        """Return usage counts keyed by each candidate's canonical_id."""

        metadata = self.get_candidate_usage_metadata(candidates)
        return {
            canonical_id: record["usage_count"]
            for canonical_id, record in metadata.items()
        }

    def get_candidate_usage_metadata(self, candidates):
        """Return usage metadata keyed by canonical question ID."""

        question_ids = [
            candidate.get("question_id")
            for candidate in candidates
            if candidate.get("question_id") is not None
        ]
        question_metadata = self.get_usage_metadata(question_ids)
        return {
            candidate["canonical_id"]: question_metadata.get(
                candidate.get("question_id"),
                {"usage_count": 0, "last_used_at": None},
            )
            for candidate in candidates
        }

    def prioritize_candidates(self, candidates, usage_counts=None):
        """Attach usage and last-used metadata without changing candidate order."""

        if usage_counts is None:
            usage_counts = self.get_candidate_usage_counts(candidates)

        for candidate in candidates:
            usage = usage_counts.get(candidate["canonical_id"], 0)
            if isinstance(usage, dict):
                candidate["_usage_count"] = usage.get("usage_count", 0)
                candidate["_last_used_at"] = usage.get("last_used_at")
            else:
                candidate["_usage_count"] = usage
                candidate["_last_used_at"] = None

        return candidates

    def get_previous_paper_signatures(self, blueprint):
        """Return prior same-configuration signatures from stored raw JSON."""

        response = (
            self.client
            .table("questionpaper")
            .select("paper_id,raw_json")
            .execute()
        )
        current_configuration = self._configuration_signature(blueprint)
        signatures = []
        for row in response.data or []:
            raw_json = row.get("raw_json") or {}
            previous_blueprint = raw_json.get("blueprint")
            selection = raw_json.get("selection")
            if not isinstance(previous_blueprint, dict) or not isinstance(selection, dict):
                continue
            if self._configuration_signature(previous_blueprint) != current_configuration:
                continue
            signature = self.paper_signature(selection)
            if signature is not None:
                signatures.append(signature)
        return signatures

    @staticmethod
    def _configuration_signature(blueprint):
        paper_info = blueprint.get("paper_information", {})
        requirements = blueprint.get("requirements", {})
        configuration = {
            "subject": paper_info.get("subject"),
            "subject_code": paper_info.get("subject_code"),
            "branch": paper_info.get("branch"),
            "semester": paper_info.get("semester"),
            "exam_type": paper_info.get("exam_type", "University"),
            "question_pattern": blueprint.get("question_pattern", {}),
            "selected_units": requirements.get("selected_units", []),
            "rua_allocation": requirements.get("rua_allocation", {}),
            "difficulty_allocation": requirements.get("difficulty_allocation", {}),
            "co_requirements": requirements.get("co_requirements", []),
        }
        return json.dumps(configuration, sort_keys=True, default=str)

    @staticmethod
    def paper_signature(selection):
        """Return stable combination and per-section sequence signatures."""

        sections = selection.get("sections")
        if not isinstance(sections, dict):
            return None
        sequence = tuple(
            (
                section_name,
                tuple(
                    question.get("canonical_id")
                    for question in section.get("questions", [])
                ),
            )
            for section_name, section in sections.items()
            if isinstance(section, dict)
            and isinstance(section.get("questions", []), list)
        )
        ids = [
            canonical_id
            for _, section_ids in sequence
            for canonical_id in section_ids
        ]
        if any(canonical_id is None for canonical_id in ids):
            return None
        return {
            "combination": frozenset(ids),
            "sequence": sequence,
        }

    def optimize_selection(self, selection, candidates, rng=None):
        """Replace reused questions with compatible fresh candidates."""

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

                replacement = rng.choice(matches) if rng is not None else matches[0]
                section["questions"][index] = replacement
                selected_ids.discard(selected["question_id"])
                selected_ids.add(replacement["question_id"])
                fresh_candidates.remove(replacement)
                replacements += 1

        return {
            "selection": selection,
            "replacements": replacements,
        }
