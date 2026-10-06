"""
Tests for Question_Paper_Validator/paper_validator.py

Covers:
  - Valid paper passing all checks
  - Section count mismatch
  - Question count mismatch per section
  - Wrong marks per question
  - Duplicate canonical IDs
  - Missing canonical ID
  - Missing RUA / difficulty / unit fields
  - RUA marks mismatch against blueprint
  - Difficulty marks mismatch against blueprint
  - Missing CO coverage
  - Question from unselected unit
  - Unexpected / missing sections
  - Invalid blueprint structure
  - Invalid selected_questions structure
  - Non-mutation of inputs
"""

import copy
import sys
import os
import unittest

# Allow direct import of paper_validator from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from paper_validator import PaperValidationError, validate_paper


# ---------------------------------------------------------------------------
# Shared fixture builders
# ---------------------------------------------------------------------------

def _make_blueprint(
    sections=None,
    rua_allocation=None,
    difficulty_allocation=None,
    co_requirements=None,
    selected_units=None,
    total_questions=3,
    generated_marks=6,
    attempted_marks=6,
):
    """
    Build a minimal valid blueprint with one section (S1: 3 questions @ 2 marks).
    Default RUA and difficulty allocations are consistent with _make_questions():
      - 3 questions, each 2 marks: Q1=R/Easy, Q2=U/Medium, Q3=A/Hard
      - actual_rua  = {R:2, U:2, A:2}  → matches rua_allocation Unit-A {R:2,U:2,A:2}
      - actual_diff = {Easy:2, Medium:2, Hard:2} → matches difficulty_allocation
    All arguments can be overridden for specific tests.
    """
    if sections is None:
        sections = {
            "S1": {
                "questions_to_generate": 3,
                "questions_to_attempt": 3,
                "marks_per_question": 2,
                "generated_section_marks": 6,
                "attempted_section_marks": 6,
            }
        }
    if rua_allocation is None:
        rua_allocation = {
            "Unit-A": {"R": 2, "U": 2, "A": 2, "Total": 6}
        }
    if difficulty_allocation is None:
        difficulty_allocation = {"Easy": 2, "Medium": 2, "Hard": 2}
    if co_requirements is None:
        co_requirements = ["CO1"]
    if selected_units is None:
        selected_units = ["Unit-A"]

    return {
        "paper_information": {
            "branch": "Test Branch",
            "semester": 3,
            "subject": "Test Subject",
            "subject_code": "TS101",
            "exam_type": "Unit Test",
            "paper_total_marks": attempted_marks,
        },
        "requirements": {
            "selected_units": selected_units,
            "rua_allocation": rua_allocation,
            "difficulty_allocation": difficulty_allocation,
            "co_requirements": co_requirements,
        },
        "question_pattern": sections,
        "calculated_values": {
            "total_questions_to_generate": total_questions,
            "generated_question_marks": generated_marks,
            "total_attempted_marks": attempted_marks,
        },
    }


def _make_questions(section_name="S1", marks=2, unit="Unit-A", co="CO1", start_id=1):
    """
    Build a selected_questions dict for a single section with 3 questions.
    Questions are spread across R/U/A and Easy/Medium/Hard so that the
    default blueprint's rua_allocation {R:2, U:2, A:2} and
    difficulty_allocation {Easy:2, Medium:2, Hard:2} are satisfied exactly.
    """
    questions = [
        {
            "canonical_id": f"CAN_{start_id:03d}",
            "question_text": f"Question {start_id}",
            "unit": unit,
            "marks": marks,
            "rua": "R",
            "difficulty": "Easy",
            "course_outcome": co,
        },
        {
            "canonical_id": f"CAN_{start_id + 1:03d}",
            "question_text": f"Question {start_id + 1}",
            "unit": unit,
            "marks": marks,
            "rua": "U",
            "difficulty": "Medium",
            "course_outcome": co,
        },
        {
            "canonical_id": f"CAN_{start_id + 2:03d}",
            "question_text": f"Question {start_id + 2}",
            "unit": unit,
            "marks": marks,
            "rua": "A",
            "difficulty": "Hard",
            "course_outcome": co,
        },
    ]
    return {"sections": {section_name: {"questions": questions}}}


def _make_valid_pair():
    """Return a (blueprint, selected_questions) pair that passes all checks."""
    bp = _make_blueprint()
    sq = _make_questions()
    return bp, sq


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestValidPaper(unittest.TestCase):

    def test_valid_paper_passes_all_checks(self):
        bp, sq = _make_valid_pair()
        result = validate_paper(bp, sq)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["errors"], [])

    def test_summary_contains_expected_fields(self):
        bp, sq = _make_valid_pair()
        result = validate_paper(bp, sq)
        summary = result["summary"]
        self.assertIn("total_questions", summary)
        self.assertIn("generated_question_marks", summary)
        self.assertIn("attempted_question_marks", summary)
        self.assertIn("unique_canonical_ids", summary)
        self.assertIn("rua_marks", summary)
        self.assertIn("difficulty_marks", summary)
        self.assertIn("covered_cos", summary)

    def test_summary_values_correct(self):
        bp, sq = _make_valid_pair()
        result = validate_paper(bp, sq)
        s = result["summary"]
        self.assertEqual(s["total_questions"], 3)
        self.assertEqual(s["generated_question_marks"], 6)
        self.assertEqual(s["unique_canonical_ids"], 3)
        self.assertIn("CO1", s["covered_cos"])

    def test_multiple_sections_valid(self):
        """Two sections with different marks — RUA and difficulty consistent with blueprint."""
        # S1: 2 questions @ 2 marks: Q1=R/Easy, Q2=U/Medium  → R=2, U=2
        # S2: 2 questions @ 4 marks: Q3=A/Hard,  Q4=R/Easy   → A=4, R=4
        # total rua: R=2+4=6, U=2, A=4  → matches rua_allocation
        # total diff: Easy=2+4=6, Medium=2, Hard=4 → matches difficulty_allocation
        bp = _make_blueprint(
            sections={
                "S1": {"questions_to_generate": 2, "questions_to_attempt": 2,
                       "marks_per_question": 2, "generated_section_marks": 4,
                       "attempted_section_marks": 4},
                "S2": {"questions_to_generate": 2, "questions_to_attempt": 2,
                       "marks_per_question": 4, "generated_section_marks": 8,
                       "attempted_section_marks": 8},
            },
            rua_allocation={"Unit-A": {"R": 6, "U": 2, "A": 4, "Total": 12}},
            difficulty_allocation={"Easy": 6, "Medium": 2, "Hard": 4},
            co_requirements=["CO1"],
            selected_units=["Unit-A"],
            total_questions=4,
            generated_marks=12,
            attempted_marks=12,
        )
        sq = {
            "sections": {
                "S1": {"questions": [
                    {"canonical_id": "A1", "question_text": "Q", "unit": "Unit-A",
                     "marks": 2, "rua": "R", "difficulty": "Easy", "course_outcome": "CO1"},
                    {"canonical_id": "A2", "question_text": "Q", "unit": "Unit-A",
                     "marks": 2, "rua": "U", "difficulty": "Medium", "course_outcome": "CO1"},
                ]},
                "S2": {"questions": [
                    {"canonical_id": "B1", "question_text": "Q", "unit": "Unit-A",
                     "marks": 4, "rua": "A", "difficulty": "Hard", "course_outcome": "CO1"},
                    {"canonical_id": "B2", "question_text": "Q", "unit": "Unit-A",
                     "marks": 4, "rua": "R", "difficulty": "Easy", "course_outcome": "CO1"},
                ]},
            }
        }
        result = validate_paper(bp, sq)
        self.assertTrue(result["valid"], result["errors"])


# ---------------------------------------------------------------------------
# Section-level errors
# ---------------------------------------------------------------------------

class TestSectionValidation(unittest.TestCase):

    def test_missing_section_produces_error(self):
        bp, _ = _make_valid_pair()
        sq = {"sections": {}}   # S1 completely absent
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Missing required section" in e for e in result["errors"]))

    def test_unexpected_section_produces_error(self):
        bp, sq = _make_valid_pair()
        sq["sections"]["EXTRA"] = {"questions": []}
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Unexpected section" in e for e in result["errors"]))

    def test_wrong_question_count_in_section(self):
        bp, sq = _make_valid_pair()
        # Remove one question — now only 2 instead of required 3
        sq["sections"]["S1"]["questions"] = sq["sections"]["S1"]["questions"][:2]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("contains" in e and "questions" in e for e in result["errors"]))


# ---------------------------------------------------------------------------
# Question-level errors
# ---------------------------------------------------------------------------

class TestQuestionValidation(unittest.TestCase):

    def test_wrong_marks_per_question(self):
        bp, sq = _make_valid_pair()
        sq["sections"]["S1"]["questions"][0]["marks"] = 99
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("marks" in e for e in result["errors"]))

    def test_missing_canonical_id(self):
        bp, sq = _make_valid_pair()
        del sq["sections"]["S1"]["questions"][0]["canonical_id"]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("canonical_id" in e for e in result["errors"]))

    def test_duplicate_canonical_id(self):
        bp, sq = _make_valid_pair()
        sq["sections"]["S1"]["questions"][1]["canonical_id"] = \
            sq["sections"]["S1"]["questions"][0]["canonical_id"]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Duplicate" in e for e in result["errors"]))

    def test_missing_rua_field(self):
        bp, sq = _make_valid_pair()
        del sq["sections"]["S1"]["questions"][0]["rua"]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("rua" in e.lower() for e in result["errors"]))

    def test_missing_difficulty_field(self):
        bp, sq = _make_valid_pair()
        del sq["sections"]["S1"]["questions"][0]["difficulty"]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("difficulty" in e.lower() for e in result["errors"]))

    def test_missing_unit_field(self):
        bp, sq = _make_valid_pair()
        del sq["sections"]["S1"]["questions"][0]["unit"]
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unit" in e.lower() for e in result["errors"]))

    def test_question_from_unselected_unit(self):
        bp, sq = _make_valid_pair()
        sq["sections"]["S1"]["questions"][0]["unit"] = "Unit-UNKNOWN"
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("unselected unit" in e for e in result["errors"]))


# ---------------------------------------------------------------------------
# Allocation mismatch errors
# ---------------------------------------------------------------------------

class TestAllocationValidation(unittest.TestCase):

    def test_rua_marks_mismatch(self):
        """Changing all questions to a single RUA tag shifts totals away from blueprint."""
        bp, sq = _make_valid_pair()
        # Default questions: R=2, U=2, A=2. Blueprint expects the same.
        # Change all to "U" → actual U=6, R=0, A=0 → mismatch on R and A.
        for q in sq["sections"]["S1"]["questions"]:
            q["rua"] = "U"
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("RUA" in e for e in result["errors"]))

    def test_difficulty_marks_mismatch(self):
        """Changing all difficulty tags to Hard shifts totals away from blueprint."""
        bp, sq = _make_valid_pair()
        # Default questions: Easy=2, Medium=2, Hard=2. Blueprint expects the same.
        # Change all to "Hard" → actual Hard=6, Easy=0, Medium=0 → mismatch.
        for q in sq["sections"]["S1"]["questions"]:
            q["difficulty"] = "Hard"
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Difficulty" in e or "difficulty" in e
                            for e in result["errors"]))

    def test_co_not_covered(self):
        """A required CO that no question covers produces an error."""
        bp, sq = _make_valid_pair()
        # Blueprint requires CO1; all questions map to CO99
        for q in sq["sections"]["S1"]["questions"]:
            q["course_outcome"] = "CO99"
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])
        self.assertTrue(any("CO1" in e for e in result["errors"]))


# ---------------------------------------------------------------------------
# Generated / attempted marks totals
# ---------------------------------------------------------------------------

class TestMarksTotals(unittest.TestCase):

    def test_total_generated_marks_mismatch(self):
        """If questions have higher marks the total won't match blueprint."""
        bp, sq = _make_valid_pair()
        for q in sq["sections"]["S1"]["questions"]:
            q["marks"] = 10   # blueprint expects 2
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])

    def test_total_generated_questions_mismatch(self):
        """Blueprint says 3 questions; providing 4 should fail."""
        bp, sq = _make_valid_pair()
        sq["sections"]["S1"]["questions"].append({
            "canonical_id": "CAN_999",
            "question_text": "Extra question",
            "unit": "Unit-A",
            "marks": 2,
            "rua": "R",
            "difficulty": "Easy",
            "course_outcome": "CO1",
        })
        result = validate_paper(bp, sq)
        self.assertFalse(result["valid"])


# ---------------------------------------------------------------------------
# Invalid structure / type errors
# ---------------------------------------------------------------------------

class TestInvalidStructure(unittest.TestCase):

    def test_non_dict_blueprint_raises(self):
        _, sq = _make_valid_pair()
        with self.assertRaises(PaperValidationError):
            validate_paper("not a dict", sq)

    def test_missing_blueprint_key_raises(self):
        bp, sq = _make_valid_pair()
        del bp["requirements"]
        with self.assertRaises(PaperValidationError):
            validate_paper(bp, sq)

    def test_non_dict_selected_questions_returns_invalid(self):
        bp, _ = _make_valid_pair()
        result = validate_paper(bp, "not a dict")
        self.assertFalse(result["valid"])
        self.assertTrue(len(result["errors"]) > 0)

    def test_empty_sections_returns_invalid(self):
        bp, _ = _make_valid_pair()
        result = validate_paper(bp, {"sections": {}})
        self.assertFalse(result["valid"])

    def test_sections_key_at_root_is_accepted(self):
        """selected_questions with 'sections' wrapper must be handled."""
        bp, sq = _make_valid_pair()
        self.assertIn("sections", sq)
        result = validate_paper(bp, sq)
        self.assertTrue(result["valid"], result["errors"])

    def test_sections_without_wrapper_is_accepted(self):
        """selected_questions as a bare {section: data} dict also works."""
        bp, sq = _make_valid_pair()
        bare = sq["sections"]   # strip the 'sections' wrapper
        result = validate_paper(bp, bare)
        self.assertTrue(result["valid"], result["errors"])


# ---------------------------------------------------------------------------
# Non-mutation
# ---------------------------------------------------------------------------

class TestNonMutation(unittest.TestCase):

    def test_blueprint_not_mutated(self):
        bp, sq = _make_valid_pair()
        original_bp = copy.deepcopy(bp)
        validate_paper(bp, sq)
        self.assertEqual(bp, original_bp)

    def test_selected_questions_not_mutated(self):
        bp, sq = _make_valid_pair()
        original_sq = copy.deepcopy(sq)
        validate_paper(bp, sq)
        self.assertEqual(sq, original_sq)


# ---------------------------------------------------------------------------
# Real sample data smoke test
# ---------------------------------------------------------------------------

class TestRealSampleData(unittest.TestCase):
    """
    Smoke-test using the actual files in sample_data/.

    NOTE: The blueprint uses section keys "Q.1"..."Q.6" (with dots).
    The selected_questions.json uses "Q1"..."Q6" (without dots).
    This is a known section-naming mismatch between the two files.
    The test documents this explicitly — it does NOT modify either file.
    """

    SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "sample_data")

    def _load(self, filename):
        import json
        path = os.path.join(self.SAMPLE_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def test_blueprint_file_loads(self):
        bp = self._load("blueprint_232145_20260827_183030_7c86.json")
        self.assertIn("paper_information", bp)
        self.assertIn("requirements", bp)
        self.assertIn("question_pattern", bp)
        self.assertIn("calculated_values", bp)

    def test_selected_questions_file_loads(self):
        sq = self._load("selected_questions.json")
        self.assertIn("sections", sq)
        self.assertEqual(len(sq["sections"]), 6)

    def test_section_name_mismatch_is_detected(self):
        """
        Blueprint sections: Q.1 Q.2 Q.3 Q.4 Q.5 Q.6
        Selected questions: Q1  Q2  Q3  Q4  Q5  Q6
        validate_paper must report these as missing/unexpected — not crash.
        """
        bp = self._load("blueprint_232145_20260827_183030_7c86.json")
        sq = self._load("selected_questions.json")
        result = validate_paper(bp, sq)
        # Must return a structured result (not raise)
        self.assertIn("valid", result)
        self.assertIn("errors", result)
        # Must be invalid because sections don't match
        self.assertFalse(result["valid"])
        # All 6 blueprint sections should be reported as missing
        missing_errors = [e for e in result["errors"] if "Missing required section" in e]
        self.assertEqual(len(missing_errors), 6,
            f"Expected 6 missing section errors, got: {result['errors']}")

    def test_section_name_mismatch_details(self):
        """Blueprint uses dot notation Q.1; verify the exact keys."""
        bp = self._load("blueprint_232145_20260827_183030_7c86.json")
        bp_sections = set(bp["question_pattern"].keys())
        self.assertEqual(bp_sections, {"Q.1", "Q.2", "Q.3", "Q.4", "Q.5", "Q.6"})

        sq = self._load("selected_questions.json")
        sq_sections = set(sq["sections"].keys())
        self.assertEqual(sq_sections, {"Q1", "Q2", "Q3", "Q4", "Q5", "Q6"})


if __name__ == "__main__":
    unittest.main()
