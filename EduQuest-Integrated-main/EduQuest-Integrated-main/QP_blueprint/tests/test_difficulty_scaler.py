"""
Tests for difficulty_scaler.scale_difficulty_allocation.

Covers:
  - Standard 70 attempted → 94 generated case
  - Different dynamic question patterns
  - Rounding with decimals and deterministic LRM tie-breaking
  - Invalid difficulty total mismatch
  - Final scaled total exactly matching generated marks
  - Original input remaining unchanged (non-mutation)
  - Edge cases: single category, zero-value category, two categories
  - All validation error paths
"""

import copy
import sys
import os
import unittest

# Allow direct import of difficulty_scaler from the parent directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from difficulty_scaler import DifficultyScalerValidationError, scale_difficulty_allocation


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make(attempted: int, generated: int, diff: dict) -> dict:
    """
    Build minimal faculty_data with a single question-pattern section where
    marks_per_question=1, so attempted == marks_attempted and
    generated == marks_generated exactly.
    """
    return {
        "difficulty_allocation": diff,
        "question_pattern": {
            "Q": {
                "questions_to_attempt":  attempted,
                "questions_to_generate": generated,
                "marks_per_question":    1,
            }
        },
    }


def _make_multi(sections: list[dict], diff: dict) -> dict:
    """
    Build faculty_data with multiple question-pattern sections.
    Each element of *sections* is:
        {"name": str, "attempt": int, "generate": int, "marks": int}
    """
    pattern = {
        s["name"]: {
            "questions_to_attempt":  s["attempt"],
            "questions_to_generate": s["generate"],
            "marks_per_question":    s["marks"],
        }
        for s in sections
    }
    return {"difficulty_allocation": diff, "question_pattern": pattern}


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------

class TestScaleDifficultyHappyPath(unittest.TestCase):

    def test_standard_70_to_94(self):
        """
        Standard OS-exam case: 70 attempted → 94 generated.
        Original: Easy=20, Medium=35, Hard=15 (sum=70).
        Scaling factor = 94/70 ≈ 1.3429.
        Exact:  Easy=26.857, Medium=47.0,  Hard=20.143
        Floors: Easy=26,     Medium=47,    Hard=20   → sum=93, budget=1
        Remainders: Easy≈0.857, Hard≈0.143, Medium=0.0
        Budget of 1 → Easy gets +1.
        The normalized result stays even and sums to 94.
        """
        data   = _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result = scale_difficulty_allocation(data)

        self.assertEqual(result["original_total_marks"],    70)
        self.assertEqual(result["generated_question_marks"], 94)
        self.assertAlmostEqual(result["scaling_factor"], 94 / 70)

        diff = result["difficulty_allocation"]
        self.assertEqual(diff["Easy"],   26)
        self.assertEqual(diff["Medium"], 48)
        self.assertEqual(diff["Hard"],   20)
        self.assertEqual(sum(diff.values()), 94)

    def test_scaled_total_exactly_equals_generated_marks(self):
        """Result must sum to generated_question_marks with no off-by-one."""
        for attempted, generated, diff in [
            (70,  94, {"Easy": 20, "Medium": 35, "Hard": 15}),
            (50,  80, {"Easy": 15, "Medium": 25, "Hard": 10}),
            (30,  46, {"Easy": 10, "Medium": 12, "Hard":  8}),
            (100, 130, {"Easy": 40, "Medium": 40, "Hard": 20}),
        ]:
            with self.subTest(attempted=attempted, generated=generated):
                data   = _make(attempted, generated, diff)
            result = scale_difficulty_allocation(data)
            total  = sum(result["difficulty_allocation"].values())
            self.assertEqual(total, generated,
                f"Total {total} ≠ generated {generated}")
            self.assertTrue(all(value % 2 == 0 for value in result["difficulty_allocation"].values()))

    def test_all_values_are_plain_integers(self):
        """Every scaled difficulty value must be type int, not float."""
        data   = _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result = scale_difficulty_allocation(data)
        for cat, val in result["difficulty_allocation"].items():
            self.assertIsInstance(val, int, f"'{cat}' = {val} is not int")

    def test_exact_factor_no_rounding_needed(self):
        """Factor = 2 exactly — all values double cleanly."""
        data   = _make(30, 60, {"Easy": 10, "Medium": 10, "Hard": 10})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(diff["Easy"],   20)
        self.assertEqual(diff["Medium"], 20)
        self.assertEqual(diff["Hard"],   20)
        self.assertEqual(sum(diff.values()), 60)

    def test_multi_section_question_pattern(self):
        """
        Multiple sections — marks are accumulated across all sections.
        Sections:
            A: attempt=5,  generate=10, marks=2  → attempted=10,  generated=20
            B: attempt=10, generate=15, marks=4  → attempted=40,  generated=60
        Total attempted=50, generated=80.
        """
        data = _make_multi(
            [
                {"name": "A", "attempt": 5,  "generate": 10, "marks": 2},
                {"name": "B", "attempt": 10, "generate": 15, "marks": 4},
            ],
            {"Easy": 15, "Medium": 25, "Hard": 10},  # sums to 50
        )
        result = scale_difficulty_allocation(data)
        self.assertEqual(result["original_total_marks"],    50)
        self.assertEqual(result["generated_question_marks"], 80)
        self.assertEqual(sum(result["difficulty_allocation"].values()), 80)

    def test_os_pattern_six_sections(self):
        """
        OPS exam pattern: Q1 (7×2=14 gen, 5×2=10 att) + Q2-Q6 (4×4×5=80 gen, 3×4×5=60 att).
        Total: attempted=70, generated=94.
        """
        data = _make_multi(
            [
                {"name": "Q1",  "attempt": 5,  "generate": 7,  "marks": 2},
                {"name": "Q2",  "attempt": 3,  "generate": 4,  "marks": 4},
                {"name": "Q3",  "attempt": 3,  "generate": 4,  "marks": 4},
                {"name": "Q4",  "attempt": 3,  "generate": 4,  "marks": 4},
                {"name": "Q5",  "attempt": 3,  "generate": 4,  "marks": 4},
                {"name": "Q6",  "attempt": 3,  "generate": 4,  "marks": 4},
            ],
            {"Easy": 20, "Medium": 35, "Hard": 15},
        )
        result = scale_difficulty_allocation(data)
        self.assertEqual(result["original_total_marks"],    70)
        self.assertEqual(result["generated_question_marks"], 94)
        self.assertEqual(sum(result["difficulty_allocation"].values()), 94)

    def test_return_shape_has_all_keys(self):
        """Return dict must have exactly the four required keys."""
        data   = _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result = scale_difficulty_allocation(data)
        for key in ("original_total_marks", "generated_question_marks",
                    "scaling_factor", "difficulty_allocation"):
            self.assertIn(key, result)


# ---------------------------------------------------------------------------
# Rounding / determinism tests
# ---------------------------------------------------------------------------

class TestScaleDifficultyRounding(unittest.TestCase):

    def test_rounding_single_unit_budget(self):
        """
        30 → 32. Apportion sixteen two-mark units proportionally.
        Easy wins the deterministic equal-remainder tie.
        """
        data   = _make(30, 32, {"Easy": 10, "Hard": 10, "Medium": 10})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(diff["Easy"],   12)
        self.assertEqual(diff["Hard"],   10)
        self.assertEqual(diff["Medium"], 10)
        self.assertEqual(sum(diff.values()), 32)

    def test_rounding_two_unit_budget(self):
        """
        20 → 22. Equal proportions yield eleven marks each, which is
        infeasible; the even-mark tie-break gives the extra two marks to A.
        """
        data   = _make(20, 22, {"A": 10, "B": 10})
        diff   = scale_difficulty_allocation(data)["difficulty_allocation"]
        self.assertEqual(diff["A"], 12)
        self.assertEqual(diff["B"], 10)

    def test_rounding_large_budget(self):
        """
        60 → 94. Scaling factor ≈ 1.5667.
        Verify only that sum equals 94 and all values are ints.
        """
        data   = _make(60, 94, {"Easy": 20, "Medium": 30, "Hard": 10})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(sum(diff.values()), 94)
        for val in diff.values():
            self.assertIsInstance(val, int)

    def test_determinism_same_input_same_output(self):
        """Two calls with identical input must produce identical output."""
        data    = _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        result1 = scale_difficulty_allocation(data)
        result2 = scale_difficulty_allocation(data)
        self.assertEqual(result1["difficulty_allocation"],
                         result2["difficulty_allocation"])

    def test_unequal_original_values_scaled_proportionally(self):
        """
        Easy=40, Medium=20, Hard=10 (total=70) → 94.
        Verify larger original categories get proportionally larger scaled values.
        """
        data   = _make(70, 94, {"Easy": 40, "Medium": 20, "Hard": 10})
        diff   = scale_difficulty_allocation(data)["difficulty_allocation"]
        # Easy should be the largest
        self.assertGreater(diff["Easy"], diff["Medium"])
        self.assertGreater(diff["Medium"], diff["Hard"])
        self.assertEqual(sum(diff.values()), 94)


# ---------------------------------------------------------------------------
# Edge-case tests
# ---------------------------------------------------------------------------

class TestScaleDifficultyEdgeCases(unittest.TestCase):

    def test_single_category_absorbs_all(self):
        """One difficulty category must receive all generated marks."""
        data   = _make(20, 24, {"OnlyLevel": 20})
        result = scale_difficulty_allocation(data)
        self.assertEqual(result["difficulty_allocation"]["OnlyLevel"], 24)

    def test_two_categories(self):
        """Works with any number of categories, not just Easy/Medium/Hard."""
        data   = _make(50, 80, {"Low": 25, "High": 25})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(sum(diff.values()), 80)
        for val in diff.values():
            self.assertIsInstance(val, int)

    def test_zero_value_category_stays_zero(self):
        """A category with original value 0 must remain 0 after scaling."""
        data   = _make(30, 46, {"Easy": 30, "Hard": 0})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(diff["Hard"], 0)
        self.assertEqual(sum(diff.values()), 46)

    def test_no_internal_choice_same_marks(self):
        """
        When generate == attempt (no internal choice), scaling factor = 1.
        Difficulty values are preserved (as integers, rounded if they were floats).
        """
        data   = _make(50, 50, {"Easy": 20, "Medium": 20, "Hard": 10})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(diff["Easy"],   20)
        self.assertEqual(diff["Medium"], 20)
        self.assertEqual(diff["Hard"],   10)
        self.assertEqual(sum(diff.values()), 50)

    def test_four_categories(self):
        """Four named categories all scale and sum correctly."""
        data   = _make(40, 60, {"VeryEasy": 10, "Easy": 10, "Hard": 10, "VeryHard": 10})
        result = scale_difficulty_allocation(data)
        diff   = result["difficulty_allocation"]
        self.assertEqual(sum(diff.values()), 60)
        for val in diff.values():
            self.assertIsInstance(val, int)


class TestEvenMarkNormalization(unittest.TestCase):

    @staticmethod
    def _case(attempted, generated, difficulty):
        return _make_multi(
            [
                {"name": "Q1", "attempt": 7, "generate": 7, "marks": 2},
                {"name": "Q2", "attempt": 20, "generate": 20, "marks": 4},
            ],
            difficulty,
        ) if attempted == generated == 94 else _make(attempted, generated, difficulty)

    def test_27_54_13_becomes_feasible_even_allocation(self):
        result = scale_difficulty_allocation(
            self._case(94, 94, {"Easy": 27, "Medium": 54, "Hard": 13})
        )
        allocation = result["difficulty_allocation"]
        self.assertEqual(allocation, {"Easy": 28, "Hard": 12, "Medium": 54})
        self.assertTrue(all(value % 2 == 0 for value in allocation.values()))
        self.assertEqual(sum(allocation.values()), 94)

    def test_already_even_allocation_remains_unchanged(self):
        original = {"Easy": 28, "Medium": 54, "Hard": 12}
        result = scale_difficulty_allocation(self._case(94, 94, original))
        self.assertEqual(result["difficulty_allocation"], original)

    def test_ratio_is_closest_among_feasible_allocations(self):
        original = {"Easy": 20, "Medium": 40, "Hard": 10}
        result = scale_difficulty_allocation(_make(70, 94, original))
        allocation = result["difficulty_allocation"]
        target = 94
        exact = {key: value * target / sum(original.values()) for key, value in original.items()}

        def deviation(candidate):
            return sum(abs(candidate[key] - exact[key]) for key in original)

        actual_deviation = deviation(allocation)
        best_deviation = min(
            deviation({"Easy": easy, "Medium": medium, "Hard": target - easy - medium})
            for easy in range(0, target + 1, 2)
            for medium in range(0, target - easy + 1, 2)
        )
        self.assertEqual(actual_deviation, best_deviation)

    def test_odd_generated_total_cannot_be_evenly_allocated(self):
        with self.assertRaises(DifficultyScalerValidationError):
            scale_difficulty_allocation(_make(30, 45, {"Easy": 10, "Medium": 12, "Hard": 8}))


# ---------------------------------------------------------------------------
# Non-mutation test
# ---------------------------------------------------------------------------

class TestScaleDifficultyNonMutation(unittest.TestCase):

    def test_original_faculty_data_unchanged(self):
        """scale_difficulty_allocation must not mutate the input dict."""
        data     = _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})
        original = copy.deepcopy(data)
        scale_difficulty_allocation(data)
        self.assertEqual(data, original)

    def test_original_diff_dict_not_shared(self):
        """Result difficulty_allocation must be a new dict, not the same object."""
        data   = _make(30, 60, {"Easy": 10, "Medium": 10, "Hard": 10})
        result = scale_difficulty_allocation(data)
        # Mutating the result must not affect the input
        result["difficulty_allocation"]["Easy"] = 999
        self.assertEqual(data["difficulty_allocation"]["Easy"], 10)


# ---------------------------------------------------------------------------
# Validation error tests
# ---------------------------------------------------------------------------

class TestScaleDifficultyValidationErrors(unittest.TestCase):

    def _base_data(self):
        return _make(70, 94, {"Easy": 20, "Medium": 35, "Hard": 15})

    def test_non_dict_input_raises(self):
        for bad in ("string", 42, None, [1, 2, 3]):
            with self.subTest(bad=bad):
                with self.assertRaises(DifficultyScalerValidationError):
                    scale_difficulty_allocation(bad)

    def test_missing_question_pattern_raises(self):
        data = {"difficulty_allocation": {"Easy": 10}}
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("question_pattern", str(ctx.exception))

    def test_missing_difficulty_allocation_raises(self):
        data = {
            "question_pattern": {
                "Q": {"questions_to_attempt": 10,
                      "questions_to_generate": 15,
                      "marks_per_question": 1}
            }
        }
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("difficulty_allocation", str(ctx.exception))

    def test_empty_difficulty_allocation_raises(self):
        data = _make(30, 45, {})
        with self.assertRaises(DifficultyScalerValidationError):
            scale_difficulty_allocation(data)

    def test_difficulty_total_mismatch_raises(self):
        """difficulty total (60) ≠ attempted marks (50) must raise."""
        data = _make(50, 80, {"Easy": 20, "Medium": 20, "Hard": 20})  # sum=60 ≠ 50
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("does not equal", str(ctx.exception))

    def test_negative_difficulty_value_raises(self):
        data = _make(30, 45, {"Easy": 40, "Hard": -10})
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("cannot be negative", str(ctx.exception))

    def test_non_numeric_difficulty_value_raises(self):
        data = _make(30, 45, {"Easy": "twenty", "Hard": 10})
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("must be a number", str(ctx.exception))

    def test_missing_section_key_raises(self):
        data = {
            "difficulty_allocation": {"Easy": 10},
            "question_pattern": {
                "Q": {"questions_to_attempt": 10, "marks_per_question": 1}
                # questions_to_generate missing
            },
        }
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("questions_to_generate", str(ctx.exception))

    def test_non_numeric_section_value_raises(self):
        data = {
            "difficulty_allocation": {"Easy": 10},
            "question_pattern": {
                "Q": {
                    "questions_to_attempt":  "ten",
                    "questions_to_generate": 15,
                    "marks_per_question":    1,
                }
            },
        }
        with self.assertRaises(DifficultyScalerValidationError) as ctx:
            scale_difficulty_allocation(data)
        self.assertIn("must be a number", str(ctx.exception))

    def test_non_dict_difficulty_allocation_raises(self):
        data = {
            "difficulty_allocation": [20, 35, 15],
            "question_pattern": {
                "Q": {"questions_to_attempt": 70,
                      "questions_to_generate": 94,
                      "marks_per_question": 1}
            },
        }
        with self.assertRaises(DifficultyScalerValidationError):
            scale_difficulty_allocation(data)

    def test_non_dict_question_pattern_raises(self):
        data = {
            "difficulty_allocation": {"Easy": 10},
            "question_pattern": "not a dict",
        }
        with self.assertRaises(DifficultyScalerValidationError):
            scale_difficulty_allocation(data)

    def test_section_details_not_dict_raises(self):
        data = {
            "difficulty_allocation": {"Easy": 10},
            "question_pattern": {"Q": "not a dict"},
        }
        with self.assertRaises(DifficultyScalerValidationError):
            scale_difficulty_allocation(data)


if __name__ == "__main__":
    unittest.main()
