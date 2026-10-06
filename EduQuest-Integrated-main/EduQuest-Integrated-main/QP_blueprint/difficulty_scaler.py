"""
difficulty_scaler.py
--------------------
Independent module that proportionally scales the difficulty_allocation
from total attempted question marks to total generated question marks.
Allocations are rounded to the feasible two-mark unit using deterministic LRM.

This module has no dependencies on any other QP_blueprint module and can
be used standalone or imported by rua_scaler.py.
"""

import math
import copy


class DifficultyScalerValidationError(ValueError):
    """Raised when input data fails validation inside the difficulty scaler."""
    pass


def _largest_remainder(values: dict, target: int) -> dict:
    """
    Distribute *target* integer marks proportionally across *values* using
    the deterministic Largest Remainder Method.

    Tie-breaking when remainders are equal:
      1. Largest remainder descending.
      2. Key name lexicographically ascending.

    Args:
        values: dict mapping category name -> numeric value (all >= 0, sum > 0).
        target: integer total the result must sum to exactly.

    Returns:
        dict mapping the same keys -> int, guaranteed to sum to *target*.
    """
    keys = sorted(values.keys())            # deterministic base order
    total = sum(values.values())            # caller must ensure > 0

    exact     = {k: values[k] * target / total for k in keys}
    floors    = {k: math.floor(exact[k])        for k in keys}
    remainders = {k: exact[k] - floors[k]       for k in keys}

    budget = int(round(target - sum(floors.values())))
    if budget < 0:
        budget = 0

    # Deterministic sort: largest remainder first, alpha key as tiebreaker
    sorted_keys = sorted(keys, key=lambda k: (-remainders[k], k))

    result = dict(floors)
    for i in range(budget):
        result[sorted_keys[i]] += 1

    return result


def scale_difficulty_allocation(faculty_data: dict) -> dict:
    """
    Proportionally scale difficulty_allocation from total attempted question
    marks to total generated question marks using the LRM.

    Does NOT mutate *faculty_data*.

    Args:
        faculty_data: dict that must contain:
            - "difficulty_allocation": dict of { category: numeric_mark, ... }
              whose values sum to attempted_question_marks.
            - "question_pattern": dict of sections, each with
              "questions_to_attempt", "questions_to_generate",
              "marks_per_question".

    Returns:
        dict:
            {
                "original_total_marks":   <int/float>,   # attempted marks
                "generated_question_marks": <int/float>, # generated marks
                "scaling_factor":         <float>,
                "difficulty_allocation":  { category: <int>, ... }
                    # values sum EXACTLY to generated_question_marks
            }

    Raises:
        DifficultyScalerValidationError: on any structural or numeric problem.

    The generated mark total must be even because each difficulty total must
    be representable in two-mark units. Among feasible allocations, the
    deterministic Largest Remainder Method minimizes proportional rounding
    deviation.
    """
    # ------------------------------------------------------------------ #
    # 1. Top-level type checks                                             #
    # ------------------------------------------------------------------ #
    if not isinstance(faculty_data, dict):
        raise DifficultyScalerValidationError(
            "Faculty data must be a dictionary."
        )

    if "question_pattern" not in faculty_data:
        raise DifficultyScalerValidationError(
            "Missing 'question_pattern' in faculty data."
        )

    if "difficulty_allocation" not in faculty_data:
        raise DifficultyScalerValidationError(
            "Missing 'difficulty_allocation' in faculty data."
        )

    question_pattern    = faculty_data["question_pattern"]
    difficulty_allocation = faculty_data["difficulty_allocation"]

    if not isinstance(question_pattern, dict):
        raise DifficultyScalerValidationError(
            "'question_pattern' must be a dictionary."
        )

    if not isinstance(difficulty_allocation, dict):
        raise DifficultyScalerValidationError(
            "'difficulty_allocation' must be a dictionary."
        )

    if not difficulty_allocation:
        raise DifficultyScalerValidationError(
            "'difficulty_allocation' must not be empty."
        )

    # ------------------------------------------------------------------ #
    # 2. Derive attempted and generated marks from question_pattern        #
    # ------------------------------------------------------------------ #
    attempted_question_marks  = 0
    generated_question_marks  = 0

    for section_name, details in question_pattern.items():
        if not isinstance(details, dict):
            raise DifficultyScalerValidationError(
                f"Question pattern section '{section_name}' must be a dictionary."
            )
        for key in ("questions_to_attempt", "questions_to_generate", "marks_per_question"):
            if key not in details:
                raise DifficultyScalerValidationError(
                    f"Missing '{key}' in question pattern section '{section_name}'."
                )
            if not isinstance(details[key], (int, float)):
                raise DifficultyScalerValidationError(
                    f"'{key}' in section '{section_name}' must be a number."
                )

        attempted_question_marks  += details["questions_to_attempt"]  * details["marks_per_question"]
        generated_question_marks  += details["questions_to_generate"] * details["marks_per_question"]

    if attempted_question_marks <= 0:
        raise DifficultyScalerValidationError(
            "Calculated attempted question marks must be greater than zero."
        )

    # ------------------------------------------------------------------ #
    # 3. Validate difficulty values                                        #
    # ------------------------------------------------------------------ #
    diff_total = 0
    for category, val in difficulty_allocation.items():
        if not isinstance(val, (int, float)):
            raise DifficultyScalerValidationError(
                f"Difficulty value for '{category}' must be a number."
            )
        if val < 0:
            raise DifficultyScalerValidationError(
                f"Difficulty value for '{category}' cannot be negative."
            )
        diff_total += val

    if abs(diff_total - attempted_question_marks) > 1e-9:
        raise DifficultyScalerValidationError(
            f"Difficulty allocation total ({diff_total}) does not equal "
            f"attempted question marks ({attempted_question_marks})."
        )

    # ------------------------------------------------------------------ #
    # 4. Scale, then ensure every category is feasible in two-mark units.   #
    # ------------------------------------------------------------------ #
    scaling_factor = generated_question_marks / attempted_question_marks

    generated_mark_target = int(round(generated_question_marks))
    if generated_mark_target % 2:
        raise DifficultyScalerValidationError(
            "Generated question marks must be even to preserve an allocation "
            "made entirely of even difficulty marks."
        )

    source_values = {k: copy.deepcopy(v) for k, v in difficulty_allocation.items()}
    scaled = _largest_remainder(source_values, generated_mark_target)

    # Keep the legacy proportional result whenever it is already feasible.
    # Otherwise apportion two-mark units directly against the original ratios;
    # this is the closest feasible allocation and keeps tie-breaking stable.
    if any(value % 2 for value in scaled.values()):
        scaled_units = _largest_remainder(source_values, generated_mark_target // 2)
        scaled = {category: 2 * units for category, units in scaled_units.items()}

    return {
        "original_total_marks":    attempted_question_marks,
        "generated_question_marks": generated_question_marks,
        "scaling_factor":           float(scaling_factor),
        "difficulty_allocation":    scaled,
    }


if __name__ == "__main__":
    # Quick manual verification — not part of any test suite.
    import json

    sample = {
        "difficulty_allocation": {"Easy": 20, "Medium": 35, "Hard": 15},
        "question_pattern": {
            "Q1":   {"questions_to_generate": 7,  "questions_to_attempt": 5,  "marks_per_question": 2},
            "Q2":   {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q3":   {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q4":   {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q5":   {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q6":   {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
        },
    }

    result = scale_difficulty_allocation(sample)
    print(json.dumps(result, indent=4))
    total = sum(result["difficulty_allocation"].values())
    print(f"Difficulty total: {total}  (expected: {result['generated_question_marks']})")
    assert total == result["generated_question_marks"], "Total mismatch!"
    print("OK")
