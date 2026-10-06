"""
rua_scaler.py
-------------
Scales the RUA allocation from total attempted question marks to total
generated question marks using proportional scaling followed by constrained
rounding to multiples of 2 and exact-sum correction.

Difficulty scaling is delegated to the independent difficulty_scaler module.
Both scaled allocations are returned together so the pipeline only needs one
call to scale_rua_allocation.
"""

import copy
import math

from QP_blueprint.difficulty_scaler import (
    DifficultyScalerValidationError,
    scale_difficulty_allocation,
)

# Re-export so callers that previously imported scale_difficulty_allocation
# from this module continue to work without changes.
__all__ = [
    "RUAScalerValidationError",
    "DifficultyScalerValidationError",
    "scale_difficulty_allocation",
    "scale_rua_allocation",
    "scale_and_round_rua",
]


class RUAScalerValidationError(ValueError):
    """Exception raised for validation errors in the RUA Scaler."""
    pass


def scale_and_round_rua(
    original_rua: dict,
    attempted_marks: int or float,
    generated_marks: int or float,
    mark_unit: int = 2,
) -> dict:
    """
    Scales and rounds an RUA allocation dictionary from attempted_marks to generated_marks,
    ensuring all values are multiples of mark_unit (default 2), non-negative, and sum exactly
    to generated_marks while preserving original proportions as closely as possible.

    Args:
        original_rua (dict): {unit: {"R": val, "U": val, "A": val, ...}}
        attempted_marks (int or float): Total attempted marks.
        generated_marks (int or float): Total generated marks.
        mark_unit (int): Mark unit granularity (default 2).

    Returns:
        dict: Scaled RUA allocation with all R, U, A values as even numbers (multiples of mark_unit)
              and matching Unit totals summing to generated_marks.
    """
    if not isinstance(original_rua, dict) or not original_rua:
        raise RUAScalerValidationError("Original RUA allocation must be a non-empty dictionary.")

    if not isinstance(attempted_marks, (int, float)) or isinstance(attempted_marks, bool) or attempted_marks <= 0:
        raise RUAScalerValidationError("Attempted marks must be a positive number.")

    if not isinstance(generated_marks, (int, float)) or isinstance(generated_marks, bool) or generated_marks <= 0:
        raise RUAScalerValidationError("Generated marks must be a positive number.")

    if mark_unit <= 0 or not isinstance(mark_unit, int) or isinstance(mark_unit, bool):
        raise RUAScalerValidationError("mark_unit must be a positive integer.")

    if int(round(generated_marks)) % mark_unit != 0:
        raise RUAScalerValidationError(
            f"Generated marks ({generated_marks}) must be a multiple of {mark_unit} "
            f"to be representable by {mark_unit}-mark questions."
        )

    # Validate individual unit components and calculate original sum
    components = ["R", "U", "A"]
    original_total_sum = 0
    for unit, details in original_rua.items():
        if not isinstance(details, dict):
            raise RUAScalerValidationError(
                f"RUA allocation for unit '{unit}' must be a dictionary."
            )
        for comp in components:
            if comp not in details:
                raise RUAScalerValidationError(
                    f"Missing component '{comp}' in RUA allocation for unit '{unit}'."
                )
            if not isinstance(details[comp], (int, float)) or isinstance(details[comp], bool):
                raise RUAScalerValidationError(
                    f"Component '{comp}' in RUA allocation for unit '{unit}' must be a number."
                )
            if details[comp] < 0:
                raise RUAScalerValidationError(
                    f"Component '{comp}' in RUA allocation for unit '{unit}' cannot be negative."
                )
            original_total_sum += details[comp]

    if abs(original_total_sum - attempted_marks) > 1e-9:
        raise RUAScalerValidationError(
            f"Original RUA allocation grand total ({original_total_sum}) does not equal "
            f"attempted question marks ({attempted_marks})."
        )

    scaling_factor = generated_marks / attempted_marks

    # Ordered list of (unit, component) variables for deterministic processing
    variables = [
        (unit, comp)
        for unit in sorted(original_rua.keys())
        for comp in components
    ]
    comp_index = {c: i for i, c in enumerate(components)}

    # Step 1: Calculate raw scaled RUA values
    # Step 2: Round every cell to the nearest multiple of mark_unit
    raw_values = {}
    current_values = {}
    for unit, comp in variables:
        val = original_rua[unit][comp]
        raw = val * scaling_factor
        rounded = int(round(raw / mark_unit)) * mark_unit
        if rounded < 0:
            rounded = 0
        raw_values[(unit, comp)] = raw
        current_values[(unit, comp)] = rounded

    # Step 3: Calculate current total and difference
    current_total = sum(current_values.values())
    difference = int(round(generated_marks - current_total))

    # Step 4: If difference > 0, add mark_unit at a time to cells causing smallest deviation
    if difference > 0:
        steps = difference // mark_unit
        for _ in range(steps):
            best_vc = min(
                variables,
                key=lambda vc: (
                    abs((current_values[vc] + mark_unit) - raw_values[vc]),
                    vc[0],
                    comp_index[vc[1]],
                ),
            )
            current_values[best_vc] += mark_unit

    # Step 5: If difference < 0, subtract mark_unit at a time without going below 0
    elif difference < 0:
        steps = abs(difference) // mark_unit
        for _ in range(steps):
            valid_candidates = [
                vc for vc in variables if current_values[vc] >= mark_unit
            ]
            if not valid_candidates:
                raise RUAScalerValidationError(
                    "Cannot reduce RUA values without causing negative allocations."
                )
            best_vc = min(
                valid_candidates,
                key=lambda vc: (
                    abs((current_values[vc] - mark_unit) - raw_values[vc]),
                    vc[0],
                    comp_index[vc[1]],
                ),
            )
            current_values[best_vc] -= mark_unit

    # Step 6 & 7: Validate and construct output dict preserving other keys
    scaled_rua_allocation = {}
    for unit in original_rua.keys():
        unit_details = {
            k: copy.deepcopy(v)
            for k, v in original_rua[unit].items()
            if k not in ("R", "U", "A", "Total")
        }
        r_val = current_values[(unit, "R")]
        u_val = current_values[(unit, "U")]
        a_val = current_values[(unit, "A")]
        tot_val = r_val + u_val + a_val

        # Safety checks
        for name, val in [("R", r_val), ("U", u_val), ("A", a_val), ("Total", tot_val)]:
            if val < 0:
                raise RUAScalerValidationError(f"Negative allocation produced for {unit} {name}: {val}")
            if val % mark_unit != 0:
                raise RUAScalerValidationError(f"Non-{mark_unit}-multiple allocation produced for {unit} {name}: {val}")

        unit_details.update({
            "R": r_val,
            "U": u_val,
            "A": a_val,
            "Total": tot_val,
        })
        scaled_rua_allocation[unit] = unit_details

    return scaled_rua_allocation


def scale_rua_allocation(faculty_data: dict) -> dict:
    """
    Dynamically scales the RUA allocation of the faculty_data from
    attempted_question_marks to generated_question_marks using proportional
    scaling followed by constrained rounding to multiples of 2.

    Also scales difficulty_allocation over the same range by delegating to
    difficulty_scaler.scale_difficulty_allocation, so both allocations are
    internally consistent with the generated question marks.

    Does not mutate faculty_data.

    Args:
        faculty_data (dict): The dictionary containing faculty inputs.

    Returns:
        dict:
            {
                "original_total_marks":    <attempted_question_marks>,
                "generated_question_marks": <generated_question_marks>,
                "scaling_factor":          <float>,
                "rua_allocation": {
                    "<unit>": {
                        "R": <int>, "U": <int>, "A": <int>, "Total": <int>,
                        ... (other keys preserved)
                    }
                },
                "difficulty_allocation": { "<category>": <int>, ... }
            }
    """
    if not isinstance(faculty_data, dict):
        raise RUAScalerValidationError("Faculty data must be a dictionary.")

    if "question_pattern" not in faculty_data:
        raise RUAScalerValidationError("Missing 'question_pattern' in faculty data.")

    if "rua_allocation" not in faculty_data:
        raise RUAScalerValidationError("Missing 'rua_allocation' in faculty data.")

    question_pattern = faculty_data["question_pattern"]
    rua_allocation   = faculty_data["rua_allocation"]

    if not isinstance(question_pattern, dict):
        raise RUAScalerValidationError("'question_pattern' must be a dictionary.")

    if not isinstance(rua_allocation, dict):
        raise RUAScalerValidationError("'rua_allocation' must be a dictionary.")

    attempted_question_marks = 0
    generated_question_marks = 0

    for section_name, details in question_pattern.items():
        if not isinstance(details, dict):
            raise RUAScalerValidationError(
                f"Question pattern section '{section_name}' details must be a dictionary."
            )
        for key in ["questions_to_attempt", "questions_to_generate", "marks_per_question"]:
            if key not in details:
                raise RUAScalerValidationError(
                    f"Missing '{key}' in question pattern section '{section_name}'."
                )
            if not isinstance(details[key], (int, float)) or isinstance(details[key], bool):
                raise RUAScalerValidationError(
                    f"'{key}' in question pattern section '{section_name}' must be a number."
                )

        attempted_question_marks += details["questions_to_attempt"]  * details["marks_per_question"]
        generated_question_marks += details["questions_to_generate"] * details["marks_per_question"]

    if attempted_question_marks <= 0:
        raise RUAScalerValidationError(
            "Calculated attempted question marks must be greater than zero."
        )

    # Scale RUA using constrained rounding to multiples of 2
    scaled_rua_allocation = scale_and_round_rua(
        original_rua=rua_allocation,
        attempted_marks=attempted_question_marks,
        generated_marks=generated_question_marks,
        mark_unit=2,
    )

    scaling_factor = generated_question_marks / attempted_question_marks

    # Delegate difficulty scaling to the independent module
    scaled_difficulty = scale_difficulty_allocation(faculty_data)["difficulty_allocation"]

    return {
        "original_total_marks":    attempted_question_marks,
        "generated_question_marks": generated_question_marks,
        "scaling_factor":          float(scaling_factor),
        "rua_allocation":          scaled_rua_allocation,
        "difficulty_allocation":   scaled_difficulty,
    }


if __name__ == "__main__":
    import json

    sample_faculty_data = {
        "total_marks": 70,
        "difficulty_allocation": {"Easy": 20, "Medium": 35, "Hard": 15},
        "rua_allocation": {
            "Unit-I":   {"R": 2, "U": 8, "A": 4, "Total": 14},
            "Unit-II":  {"R": 4, "U": 4, "A": 6, "Total": 14},
            "Unit-III": {"R": 2, "U": 6, "A": 8, "Total": 16},
            "Unit-IV":  {"R": 2, "U": 6, "A": 8, "Total": 16},
            "Unit-V":   {"R": 2, "U": 4, "A": 4, "Total": 10},
        },
        "question_pattern": {
            "Q1": {"questions_to_generate": 7,  "questions_to_attempt": 5,  "marks_per_question": 2},
            "Q2": {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q3": {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q4": {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q5": {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
            "Q6": {"questions_to_generate": 4,  "questions_to_attempt": 3,  "marks_per_question": 4},
        },
    }

    try:
        result = scale_rua_allocation(sample_faculty_data)
        print(json.dumps(result, indent=4))
        rua_total  = sum(d["Total"] for d in result["rua_allocation"].values())
        diff_total = sum(result["difficulty_allocation"].values())
        print(f"RUA total:        {rua_total}   (expected: 94)")
        print(f"Difficulty total: {diff_total}  (expected: 94)")
    except (RUAScalerValidationError, DifficultyScalerValidationError) as e:
        print(f"Validation error: {e}")

