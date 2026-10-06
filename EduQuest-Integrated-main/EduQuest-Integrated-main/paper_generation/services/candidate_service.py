"""Candidate-question services for paper generation."""


class CandidateService:
	def get_candidates(self, questions, blueprint):
		selected_units = blueprint["requirements"]["selected_units"]

		allowed_marks = set()
		for section in blueprint["question_pattern"].values():
			allowed_marks.add(section["marks_per_question"])

		candidates = []
		for question in questions:
			if question["unit"] not in selected_units:
				continue
			if question["marks"] not in allowed_marks:
				continue
			candidates.append(question)
		return candidates
