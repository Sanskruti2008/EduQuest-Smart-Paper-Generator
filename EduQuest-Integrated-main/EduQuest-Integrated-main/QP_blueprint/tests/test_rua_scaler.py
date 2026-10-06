import unittest
import sys
import os
import copy

# Add the parent directory to sys.path to allow importing rua_scaler directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rua_scaler import (
    scale_rua_allocation,
    scale_and_round_rua,
    scale_difficulty_allocation,
    RUAScalerValidationError,
)
from difficulty_scaler import DifficultyScalerValidationError


class TestRUAScaler(unittest.TestCase):

    def get_standard_faculty_data(self):
        """Helper to return a copy of the standard faculty data (70 attempted, 94 generated)"""
        return {
            "total_marks": 70,
            "difficulty_allocation": {
                "Easy": 20,
                "Medium": 35,
                "Hard": 15
            },
            "rua_allocation": {
                "Unit-I": {"R": 2, "U": 8, "A": 4, "Total": 14},
                "Unit-II": {"R": 4, "U": 4, "A": 6, "Total": 14},
                "Unit-III": {"R": 2, "U": 6, "A": 8, "Total": 16},
                "Unit-IV": {"R": 2, "U": 6, "A": 8, "Total": 16},
                "Unit-V": {"R": 2, "U": 4, "A": 4, "Total": 10}
            },
            "question_pattern": {
                "Q1": {
                    "questions_to_generate": 7,
                    "questions_to_attempt": 5,
                    "marks_per_question": 2
                },
                "Q2-Q6": {
                    "questions_to_generate": 20,
                    "questions_to_attempt": 15,
                    "marks_per_question": 4
                }
            }
        }

    # ==========================================
    # Test 1: Final Exam (Attempted = 70, Generated = 94)
    # ==========================================
    def test_final_exam_even_scaling(self):
        """
        Test 1: Final Exam
        Input: Attempted = 70, Generated = 94
        Verify: sum(RUA) == 94 and every R/U/A value is even.
        """
        data = self.get_standard_faculty_data()
        result = scale_rua_allocation(data)

        self.assertEqual(result["original_total_marks"], 70)
        self.assertEqual(result["generated_question_marks"], 94)
        self.assertAlmostEqual(result["scaling_factor"], 94 / 70)

        rua = result["rua_allocation"]
        grand_total = 0
        for unit, details in rua.items():
            for key in ["R", "U", "A"]:
                val = details[key]
                self.assertIsInstance(val, int, f"{key} in {unit} must be int")
                self.assertGreaterEqual(val, 0, f"{key} in {unit} cannot be negative")
                self.assertEqual(val % 2, 0, f"{key} in {unit} must be even (got {val})")

            unit_total = details["Total"]
            self.assertEqual(details["R"] + details["U"] + details["A"], unit_total)
            self.assertEqual(unit_total % 2, 0, f"Unit total for {unit} must be even (got {unit_total})")
            grand_total += unit_total

        self.assertEqual(grand_total, 94, "Grand total of RUA allocation must equal 94")

    # ==========================================
    # Test 2: Periodic Test (Attempted = 30, Generated = 40)
    # ==========================================
    def test_periodic_test_even_scaling(self):
        """
        Test 2: Periodic Test
        Input: Attempted = 30, Generated = 40
        Verify: sum(RUA) == 40 and every R/U/A value is even.
        """
        data = {
            "total_marks": 30,
            "difficulty_allocation": {"Easy": 10, "Medium": 10, "Hard": 10},
            "rua_allocation": {
                "Unit-I": {"R": 4, "U": 6, "A": 5, "Total": 15},
                "Unit-II": {"R": 3, "U": 7, "A": 5, "Total": 15}
            },
            "question_pattern": {
                "Q1": {
                    "questions_to_generate": 6,
                    "questions_to_attempt": 5,
                    "marks_per_question": 2
                },
                "Q2": {
                    "questions_to_generate": 7,
                    "questions_to_attempt": 5,
                    "marks_per_question": 4
                }
            }
        }
        # Attempted: 5 * 2 + 5 * 4 = 30 marks
        # Generated: 6 * 2 + 7 * 4 = 40 marks
        result = scale_rua_allocation(data)
        self.assertEqual(result["original_total_marks"], 30)
        self.assertEqual(result["generated_question_marks"], 40)

        rua = result["rua_allocation"]
        grand_total = 0
        for unit, details in rua.items():
            for key in ["R", "U", "A"]:
                val = details[key]
                self.assertIsInstance(val, int)
                self.assertGreaterEqual(val, 0)
                self.assertEqual(val % 2, 0, f"{key} in {unit} must be even (got {val})")
            unit_total = details["Total"]
            self.assertEqual(details["R"] + details["U"] + details["A"], unit_total)
            self.assertEqual(unit_total % 2, 0)
            grand_total += unit_total

        self.assertEqual(grand_total, 40, "Grand total must equal 40")

    # ==========================================
    # Test 3: Odd allocation correction
    # ==========================================
    def test_odd_allocation_correction(self):
        """
        Test 3: Odd allocation correction
        Give the scaler RUA values that would produce odd scaled values under normal scaling.
        Verify that the final blueprint contains no odd values.
        """
        data = {
            "total_marks": 70,
            "difficulty_allocation": {"Easy": 20, "Medium": 35, "Hard": 15},
            "rua_allocation": {
                "Unit-I": {"R": 3, "U": 5, "A": 6, "Total": 14},
                "Unit-II": {"R": 5, "U": 5, "A": 11, "Total": 21},
                "Unit-III": {"R": 3, "U": 7, "A": 5, "Total": 15},
                "Unit-IV": {"R": 3, "U": 7, "A": 10, "Total": 20}
            },
            "question_pattern": {
                "Q1": {"questions_to_generate": 7, "questions_to_attempt": 5, "marks_per_question": 2},
                "Q2-Q6": {"questions_to_generate": 20, "questions_to_attempt": 15, "marks_per_question": 4}
            }
        }
        result = scale_rua_allocation(data)
        self.assertEqual(result["generated_question_marks"], 94)

        rua = result["rua_allocation"]
        grand_total = 0
        for unit, details in rua.items():
            for comp in ["R", "U", "A"]:
                val = details[comp]
                self.assertEqual(val % 2, 0, f"Component {comp} in {unit} must not be odd (got {val})")
            grand_total += details["Total"]

        self.assertEqual(grand_total, 94)

    # ==========================================
    # Test 4: Exact total preservation
    # ==========================================
    def test_exact_total_preservation(self):
        """
        Test 4: Exact total
        Verify that constrained rounding never changes the required generated total across diverse inputs.
        """
        patterns = [
            (70, 94),
            (30, 40),
            (50, 80),
            (60, 84),
        ]
        for attempted, generated in patterns:
            data = {
                "total_marks": attempted,
                "difficulty_allocation": {"Easy": attempted // 3, "Medium": attempted // 3, "Hard": attempted - 2 * (attempted // 3)},
                "rua_allocation": {
                    "Unit-I": {"R": attempted // 4, "U": attempted // 4, "A": attempted // 4, "Total": 3 * (attempted // 4)},
                    "Unit-II": {"R": attempted - 3 * (attempted // 4), "U": 0, "A": 0, "Total": attempted - 3 * (attempted // 4)}
                },
                "question_pattern": {
                    "SecA": {"questions_to_generate": generated // 2, "questions_to_attempt": attempted // 2, "marks_per_question": 2}
                }
            }
            result = scale_rua_allocation(data)
            rua_sum = sum(u["Total"] for u in result["rua_allocation"].values())
            self.assertEqual(rua_sum, generated, f"Failed exact total for {attempted} -> {generated}")

    # ==========================================
    # Test 5: Negative protection
    # ==========================================
    def test_negative_protection(self):
        """
        Test 5: Negative protection
        Verify that correction logic never produces negative RUA allocations even with 0-value components.
        """
        data = {
            "total_marks": 70,
            "difficulty_allocation": {"Easy": 20, "Medium": 35, "Hard": 15},
            "rua_allocation": {
                "Unit-I": {"R": 0, "U": 10, "A": 10, "Total": 20},
                "Unit-II": {"R": 0, "U": 0, "A": 20, "Total": 20},
                "Unit-III": {"R": 10, "U": 10, "A": 10, "Total": 30}
            },
            "question_pattern": {
                "Q1": {"questions_to_generate": 7, "questions_to_attempt": 5, "marks_per_question": 2},
                "Q2-Q6": {"questions_to_generate": 20, "questions_to_attempt": 15, "marks_per_question": 4}
            }
        }
        result = scale_rua_allocation(data)
        rua = result["rua_allocation"]
        for unit, details in rua.items():
            for comp in ["R", "U", "A", "Total"]:
                self.assertGreaterEqual(details[comp], 0, f"{comp} in {unit} became negative: {details[comp]}")
                self.assertEqual(details[comp] % 2, 0, f"{comp} in {unit} must be even")

        grand_total = sum(u["Total"] for u in rua.values())
        self.assertEqual(grand_total, 94)

    # ==========================================
    # Helper Function Tests: scale_and_round_rua
    # ==========================================
    def test_scale_and_round_rua_direct(self):
        """Test scale_and_round_rua called directly with various inputs."""
        original_rua = {
            "Unit-I": {"R": 2, "U": 8, "A": 4, "Total": 14},
            "Unit-II": {"R": 4, "U": 4, "A": 6, "Total": 14},
            "Unit-III": {"R": 2, "U": 6, "A": 8, "Total": 16},
            "Unit-IV": {"R": 2, "U": 6, "A": 8, "Total": 16},
            "Unit-V": {"R": 2, "U": 4, "A": 4, "Total": 10}
        }
        scaled = scale_and_round_rua(original_rua, 70, 94, mark_unit=2)
        total = sum(u["Total"] for u in scaled.values())
        self.assertEqual(total, 94)
        for unit, details in scaled.items():
            for comp in ["R", "U", "A", "Total"]:
                self.assertEqual(details[comp] % 2, 0)

    # ==========================================
    # Structural and Regression Tests
    # ==========================================
    def test_original_data_non_mutation(self):
        """Test that scale_rua_allocation does not mutate the original faculty_data input dictionary."""
        data = self.get_standard_faculty_data()
        data_copy = copy.deepcopy(data)

        scale_rua_allocation(data)

        # Verify the original dictionary is completely unchanged
        self.assertEqual(data, data_copy)

    def test_rua_total_mismatch_raises(self):
        """Test that validation fails when RUA total sum does not equal attempted_question_marks."""
        data = self.get_standard_faculty_data()
        data["question_pattern"]["Q1"]["questions_to_attempt"] = 6  # 72 attempted instead of 70

        with self.assertRaises(RUAScalerValidationError) as context:
            scale_rua_allocation(data)

        self.assertIn("Original RUA allocation grand total", str(context.exception))

    def test_non_dict_input_raises(self):
        with self.assertRaises(RUAScalerValidationError):
            scale_rua_allocation("not a dict")

    def test_missing_rua_allocation_raises(self):
        data = self.get_standard_faculty_data()
        del data["rua_allocation"]
        with self.assertRaises(RUAScalerValidationError):
            scale_rua_allocation(data)

    def test_missing_question_pattern_raises(self):
        data = self.get_standard_faculty_data()
        del data["question_pattern"]
        with self.assertRaises(RUAScalerValidationError):
            scale_rua_allocation(data)

    def test_scale_rua_allocation_includes_scaled_difficulty(self):
        """scale_rua_allocation result must include difficulty_allocation summing to generated_question_marks."""
        data = self.get_standard_faculty_data()
        result = scale_rua_allocation(data)

        self.assertIn("difficulty_allocation", result)
        diff = result["difficulty_allocation"]

        for cat, val in diff.items():
            self.assertIsInstance(val, int, f"difficulty '{cat}' must be int, got {type(val)}")

        self.assertEqual(sum(diff.values()), result["generated_question_marks"])


class TestDifficultyScaler(unittest.TestCase):
    """Tests for the standalone scale_difficulty_allocation function."""

    def _make_data(self, attempted, generated, diff):
        return {
            "difficulty_allocation": diff,
            "question_pattern": {
                "Q": {
                    "questions_to_attempt": attempted,
                    "questions_to_generate": generated,
                    "marks_per_question": 1,
                }
            },
        }

    def test_total_equals_generated_marks(self):
        data = self._make_data(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result = scale_difficulty_allocation(data)
        self.assertEqual(sum(result["difficulty_allocation"].values()), 94)

    def test_all_values_are_integers(self):
        data = self._make_data(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result = scale_difficulty_allocation(data)
        for cat, val in result["difficulty_allocation"].items():
            self.assertIsInstance(val, int, f"'{cat}' must be int")

    def test_does_not_mutate_input(self):
        data = self._make_data(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        original = copy.deepcopy(data)
        scale_difficulty_allocation(data)
        self.assertEqual(data, original)


if __name__ == "__main__":
    unittest.main()
