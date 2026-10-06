"""
Tests for blueprint_validator.validate_blueprint, focusing on difficulty_allocation
and rua_allocation validation against generated_question_marks, even value constraints,
non-negative checks, and paper-pattern feasibility.
"""
import sys
import os
import copy
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blueprint_validator import validate_blueprint


def _make_valid_blueprint(
    paper_total=70,
    generated_marks=94,
    attempted_marks=70,
    diff=None,
    rua=None,
):
    """
    Build a minimal but structurally complete valid blueprint.

    By default:
      - paper_total_marks = 70  (attempted)
      - generated_question_marks = 94
      - difficulty values sum to 94  (generated)
      - RUA values are even numbers summing to 94 (generated)
    """
    if diff is None:
        diff = {"Easy": 27, "Medium": 50, "Hard": 17}   # sums to 94

    if rua is None:
        rua = {
            "Unit-I": {"R": 30, "U": 40, "A": 24, "Total": 94},
        }

    return {
        "paper_information": {
            "branch": "Test Branch",
            "semester": 3,
            "subject": "Test Subject",
            "subject_code": "TS101",
            "exam_type": "Unit Test",
            "paper_total_marks": paper_total,
        },
        "requirements": {
            "selected_units": list(rua.keys()),
            "rua_allocation": rua,
            "difficulty_allocation": diff,
            "co_requirements": ["CO1"],
        },
        "question_pattern": {
            "Q1": {
                "questions_to_generate": generated_marks,
                "questions_to_attempt": attempted_marks,
                "marks_per_question": 1,
                "generated_section_marks": generated_marks,
                "attempted_section_marks": attempted_marks,
            }
        },
        "calculated_values": {
            "total_questions_to_generate": generated_marks,
            "generated_question_marks": generated_marks,
            "total_attempted_marks": attempted_marks,
        },
    }


class TestBlueprintValidatorDifficulty(unittest.TestCase):

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_valid_blueprint_passes(self):
        bp = _make_valid_blueprint()
        result = validate_blueprint(bp)
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["errors"], [])

    def test_difficulty_totalling_generated_marks_passes(self):
        """Difficulty sum == generated_question_marks (94) must pass."""
        bp = _make_valid_blueprint(
            paper_total=70, generated_marks=94, attempted_marks=70,
            diff={"Easy": 27, "Medium": 50, "Hard": 17},   # 94
        )
        result = validate_blueprint(bp)
        self.assertTrue(result["valid"], result["errors"])

    def test_equal_paper_and_generated_marks_passes(self):
        """When generate == attempt (no internal choice), difficulty == paper_total is also valid."""
        bp = _make_valid_blueprint(
            paper_total=50, generated_marks=50, attempted_marks=50,
            diff={"Easy": 15, "Medium": 20, "Hard": 15},   # 50
            rua={"Unit-I": {"R": 10, "U": 20, "A": 20, "Total": 50}}
        )
        result = validate_blueprint(bp)
        self.assertTrue(result["valid"], result["errors"])

    # ------------------------------------------------------------------
    # Difficulty total mismatch
    # ------------------------------------------------------------------

    def test_difficulty_totalling_attempted_marks_fails_when_different(self):
        """
        Difficulty summing to attempted (70) but generated is 94 must FAIL.
        This is the key regression guard for the new behavior.
        """
        bp = _make_valid_blueprint(
            paper_total=70, generated_marks=94, attempted_marks=70,
            diff={"Easy": 20, "Medium": 35, "Hard": 15},   # 70, not 94
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(
            any("94" in e for e in result["errors"]),
            f"Expected error mentioning 94, got: {result['errors']}",
        )

    def test_difficulty_total_wrong_value_fails(self):
        """Any total that doesn't match generated_question_marks must fail."""
        bp = _make_valid_blueprint(
            paper_total=70, generated_marks=94, attempted_marks=70,
            diff={"Easy": 10, "Medium": 10, "Hard": 10},   # 30
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    # ------------------------------------------------------------------
    # Structural / field errors
    # ------------------------------------------------------------------

    def test_missing_difficulty_level_fails(self):
        bp = _make_valid_blueprint()
        del bp["requirements"]["difficulty_allocation"]["Hard"]
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Hard" in e for e in result["errors"]))

    def test_negative_difficulty_value_fails(self):
        bp = _make_valid_blueprint()
        bp["requirements"]["difficulty_allocation"]["Hard"] = -5
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_missing_difficulty_allocation_fails(self):
        bp = _make_valid_blueprint()
        del bp["requirements"]["difficulty_allocation"]
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])


class TestBlueprintValidatorRUA(unittest.TestCase):
    """Tests for RUA validation in validate_blueprint."""

    def test_valid_rua_passes(self):
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": 10, "U": 20, "A": 10, "Total": 40},
                "Unit-II": {"R": 14, "U": 20, "A": 20, "Total": 54},
            }
        )
        result = validate_blueprint(bp)
        self.assertTrue(result["valid"], result["errors"])

    def test_odd_rua_component_fails(self):
        """Odd RUA values must be rejected."""
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": 3, "U": 47, "A": 44, "Total": 94},
            }
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(any("even" in e.lower() for e in result["errors"]))

    def test_odd_unit_total_fails(self):
        """Odd unit total must be rejected."""
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": 30, "U": 40, "A": 24, "Total": 95},
            }
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_negative_rua_component_fails(self):
        """Negative RUA value must be rejected."""
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": -2, "U": 48, "A": 48, "Total": 94},
            }
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(any("negative" in e.lower() for e in result["errors"]))

    def test_rua_sum_mismatch_fails(self):
        """RUA grand total not matching generated_question_marks must be rejected."""
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": 20, "U": 20, "A": 20, "Total": 60},  # 60 != 94
            }
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(any("grand total" in e.lower() or "94" in e for e in result["errors"]))

    def test_rua_unit_component_sum_mismatch_fails(self):
        """Unit Total != R + U + A must be rejected."""
        bp = _make_valid_blueprint(
            rua={
                "Unit-I": {"R": 30, "U": 40, "A": 24, "Total": 90},  # 30+40+24 = 94 != 90
            }
        )
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_missing_unit_in_rua_fails(self):
        """Selected units must be present in rua_allocation."""
        bp = _make_valid_blueprint()
        bp["requirements"]["selected_units"].append("Unit-II")
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])
        self.assertTrue(any("Unit-II" in e for e in result["errors"]))

    def test_missing_rua_allocation_fails(self):
        bp = _make_valid_blueprint()
        del bp["requirements"]["rua_allocation"]
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])


class TestBlueprintValidatorExistingChecks(unittest.TestCase):
    """Smoke-test existing checks still pass after RUA validation addition."""

    def test_missing_paper_information_fails(self):
        bp = _make_valid_blueprint()
        del bp["paper_information"]
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_zero_paper_total_marks_fails(self):
        bp = _make_valid_blueprint(paper_total=0, generated_marks=0, attempted_marks=0,
                                   diff={"Easy": 0, "Medium": 0, "Hard": 0})
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_empty_selected_units_fails(self):
        bp = _make_valid_blueprint()
        bp["requirements"]["selected_units"] = []
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_empty_co_requirements_fails(self):
        bp = _make_valid_blueprint()
        bp["requirements"]["co_requirements"] = []
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_section_marks_mismatch_fails(self):
        bp = _make_valid_blueprint()
        bp["question_pattern"]["Q1"]["generated_section_marks"] = 999
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_questions_to_attempt_exceeds_generate_fails(self):
        bp = _make_valid_blueprint(
            paper_total=50, generated_marks=50, attempted_marks=50,
            diff={"Easy": 15, "Medium": 20, "Hard": 15},
            rua={"Unit-I": {"R": 10, "U": 20, "A": 20, "Total": 50}}
        )
        bp["question_pattern"]["Q1"]["questions_to_attempt"] = 999
        result = validate_blueprint(bp)
        self.assertFalse(result["valid"])

    def test_validate_blueprint_does_not_mutate(self):
        bp = _make_valid_blueprint()
        original = copy.deepcopy(bp)
        validate_blueprint(bp)
        self.assertEqual(bp, original)


if __name__ == "__main__":
    unittest.main()
