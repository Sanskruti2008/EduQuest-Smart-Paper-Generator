"""Regression coverage for global RUA/question-pattern compatibility repair."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from rua_pattern_compatibility import (  # noqa: E402
    _can_compose_cells,
    _compatible,
    _unit_candidate_score,
    make_rua_pattern_compatible,
)


def advanced_java_blueprint():
    allocation = {
        "Unit-I": (2, 6, 6, 14),
        "Unit-II": (6, 6, 10, 22),
        "Unit-III": (6, 6, 10, 22),
        "Unit-IV": (2, 6, 10, 18),
        "Unit-V": (2, 6, 10, 18),
    }
    return {
        "paper_information": {"subject": "Advanced Java", "paper_total_marks": 70},
        "requirements": {
            "rua_allocation": {
                unit: {"R": r, "U": u, "A": a, "Total": total}
                for unit, (r, u, a, total) in allocation.items()
            },
            "selected_units": list(allocation),
            "difficulty_allocation": {"Easy": 30, "Medium": 34, "Hard": 30},
            "co_requirements": ["CO1", "CO2"],
        },
        "instructions": ["Test fixture"],
        "question_pattern": {
            "Q1": {"questions_to_generate": 7, "questions_to_attempt": 5,
                   "marks_per_question": 2, "generated_section_marks": 14,
                   "attempted_section_marks": 10},
            "Q2": {"questions_to_generate": 20, "questions_to_attempt": 15,
                   "marks_per_question": 4, "generated_section_marks": 80,
                   "attempted_section_marks": 60},
        },
        "calculated_values": {
            "total_questions_to_generate": 27,
            "generated_question_marks": 94,
            "total_attempted_marks": 70,
        },
    }


BENCHMARK = {
    "Unit-I": (2, 4, 8, 14),
    "Unit-II": (6, 8, 8, 22),
    "Unit-III": (4, 8, 10, 22),
    "Unit-IV": (2, 8, 8, 18),
    "Unit-V": (2, 6, 10, 18),
}


def install_allocation(blueprint, allocation):
    blueprint["requirements"]["rua_allocation"] = {
        unit: {"R": r, "U": u, "A": a, "Total": total}
        for unit, (r, u, a, total) in allocation.items()
    }


class TestRUAPatternCompatibility(unittest.TestCase):
    def test_original_advanced_java_allocation_is_incompatible(self):
        blueprint = advanced_java_blueprint()
        self.assertFalse(_compatible(
            blueprint, blueprint["requirements"]["rua_allocation"]
        ))

    def test_global_coin_inventory_requires_exact_capacities(self):
        inventory = ((2, 7), (4, 20))
        self.assertTrue(_can_compose_cells([2] * 7 + [4] * 20, inventory))
        self.assertFalse(_can_compose_cells([2] * 8 + [4] * 19, inventory))

    def test_known_compatible_allocation_is_left_unchanged(self):
        blueprint = advanced_java_blueprint()
        install_allocation(blueprint, BENCHMARK)
        result = make_rua_pattern_compatible(blueprint)
        self.assertEqual(result, blueprint)

    def test_multiple_candidates_rank_minimal_deviation_first(self):
        original = (2, 6, 6)
        unchanged = _unit_candidate_score(original, original, 14)
        changed_but_balanced = _unit_candidate_score((4, 4, 6), original, 14)
        self.assertLess(unchanged, changed_but_balanced)

    def test_balance_breaks_equal_deviation_tie(self):
        original = (2, 6, 6)
        balanced = _unit_candidate_score((2, 4, 8), original, 14)
        concentrated = _unit_candidate_score((0, 8, 6), original, 14)
        self.assertEqual(balanced[0], concentrated[0])
        self.assertLess(balanced, concentrated)

    def test_repair_optimizes_whole_allocation_not_first_match(self):
        blueprint = advanced_java_blueprint()
        result = make_rua_pattern_compatible(blueprint)
        self.assertNotEqual(
            result["requirements"]["rua_allocation"],
            {
                "Unit-I": {"R": 2, "U": 6, "A": 6, "Total": 14},
                "Unit-II": {"R": 6, "U": 4, "A": 12, "Total": 22},
                "Unit-III": {"R": 6, "U": 4, "A": 12, "Total": 22},
                "Unit-IV": {"R": 2, "U": 4, "A": 12, "Total": 18},
                "Unit-V": {"R": 2, "U": 4, "A": 12, "Total": 18},
            },
        )
        self.assertTrue(_compatible(result, result["requirements"]["rua_allocation"]))

    def test_repair_scores_at_least_as_well_as_the_reference_benchmark(self):
        blueprint = advanced_java_blueprint()
        repaired = make_rua_pattern_compatible(blueprint)["requirements"]["rua_allocation"]
        original = blueprint["requirements"]["rua_allocation"]

        def aggregate_score(allocation):
            deviation = balance = spread = 0
            for unit, details in allocation.items():
                values = tuple(details[c] for c in ("R", "U", "A"))
                score = _unit_candidate_score(values, tuple(original[unit][c] for c in ("R", "U", "A")), details["Total"])
                deviation += score[0]
                balance += score[1]
                spread += score[2]
            return deviation, balance, spread

        self.assertLessEqual(aggregate_score(repaired), aggregate_score({
            unit: {"R": values[0], "U": values[1], "A": values[2], "Total": values[3]}
            for unit, values in BENCHMARK.items()
        }))

    def test_unit_totals_and_other_blueprint_fields_are_preserved(self):
        blueprint = advanced_java_blueprint()
        original = copy.deepcopy(blueprint)
        result = make_rua_pattern_compatible(blueprint)
        for unit, details in original["requirements"]["rua_allocation"].items():
            repaired = result["requirements"]["rua_allocation"][unit]
            self.assertEqual(sum(repaired[c] for c in ("R", "U", "A")), details["Total"])
        self.assertEqual(result["question_pattern"], original["question_pattern"])
        self.assertEqual(result["calculated_values"], original["calculated_values"])
        for key in ("paper_information", "instructions"):
            self.assertEqual(result[key], original[key])
        self.assertEqual(blueprint, original)  # non-mutating

    def test_deterministic_output(self):
        blueprint = advanced_java_blueprint()
        first = make_rua_pattern_compatible(blueprint)
        second = make_rua_pattern_compatible(blueprint)
        self.assertEqual(first, second)

    def test_generic_synthetic_pattern(self):
        blueprint = {
            "requirements": {"rua_allocation": {
                "Alpha": {"R": 3, "U": 6, "A": 9, "Total": 18},
                "Beta": {"R": 3, "U": 6, "A": 9, "Total": 18},
            }},
            "question_pattern": {
                "S1": {"questions_to_generate": 4, "marks_per_question": 3},
                "S2": {"questions_to_generate": 4, "marks_per_question": 6},
            },
        }
        self.assertTrue(_compatible(blueprint, blueprint["requirements"]["rua_allocation"]))
        self.assertEqual(make_rua_pattern_compatible(blueprint), blueprint)

    def test_engine_has_no_question_bank_or_database_dependencies(self):
        source = Path(__file__).resolve().parents[1] / "rua_pattern_compatibility.py"
        text = source.read_text(encoding="utf-8").lower()
        for forbidden in ("psycopg", "chromadb", "candidate_service", "selection_service", "embedding"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
