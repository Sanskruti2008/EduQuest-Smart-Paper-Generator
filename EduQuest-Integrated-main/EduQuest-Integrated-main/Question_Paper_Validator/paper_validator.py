from collections import Counter, defaultdict
from datetime import datetime
import json
from pathlib import Path
import re
import sys


class PaperValidationError(ValueError):
    """Raised when the paper or blueprint structure is invalid."""
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_SAMPLE_DATA = Path(__file__).resolve().parent / "sample_data"
FORMATTER_ROOT = PROJECT_ROOT / "Question_Paper_Formatter"
FORMATTER_OUTPUT = FORMATTER_ROOT / "output"
BLUEPRINT_DIRECTORIES = (
    VALIDATOR_SAMPLE_DATA,
    FORMATTER_ROOT / "sample_data",
    PROJECT_ROOT / "QP_blueprint" / "output",
    PROJECT_ROOT / "eduquest-backend" / "output" / "blueprints",
)


def _newest_file(paths):
    """Return the most recently modified file, with a stable name tie-break."""
    existing = [path for path in paths if path.is_file()]
    return max(existing, key=lambda path: (path.stat().st_mtime_ns, path.name), default=None)


def find_latest_selected_questions(sample_data_dir=VALIDATOR_SAMPLE_DATA):
    """Find the newest selected_questions*.json file in the validator sample data."""
    return _newest_file(sample_data_dir.glob("selected_questions*.json"))


def find_blueprints_for(selected_questions, directories=BLUEPRINT_DIRECTORIES):
    """Return matching-subject Blueprints, newest first, from project output folders."""
    paper_info = selected_questions.get("paper_information", {})
    if not isinstance(paper_info, dict):
        return []
    subject_code = str(paper_info.get("subject_code", "")).strip()
    subject = str(paper_info.get("subject", "")).strip().casefold()
    candidates = {}

    for directory in directories:
        if not directory.exists():
            continue
        for path in directory.glob("blueprint*.json"):
            try:
                with path.open(encoding="utf-8") as handle:
                    blueprint = json.load(handle)
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(blueprint, dict):
                continue
            blueprint_info = blueprint.get("paper_information", {})
            if not isinstance(blueprint_info, dict):
                continue
            code_matches = (
                subject_code
                and str(blueprint_info.get("subject_code", "")).strip() == subject_code
            )
            subject_matches = (
                not subject_code
                and subject
                and str(blueprint_info.get("subject", "")).strip().casefold() == subject
            )
            if code_matches or subject_matches:
                candidates[path.resolve()] = (path, blueprint)

    ordered = sorted(
        candidates.values(),
        key=lambda item: (item[0].stat().st_mtime_ns, item[0].name),
        reverse=True,
    )
    return ordered


def _get_question_sections(selected_questions_data):
    """
    Supports either:
    1. A dictionary containing section names mapped to question lists
    2. A dictionary containing a 'sections' key
    """

    if not isinstance(selected_questions_data, dict):
        raise PaperValidationError(
            "selected_questions data must be a dictionary."
        )

    if "sections" in selected_questions_data:
        sections = selected_questions_data["sections"]
    else:
        sections = selected_questions_data

    if not isinstance(sections, dict):
        raise PaperValidationError(
            "Selected question sections must be a dictionary."
        )

    return sections


def _extract_questions(section_data, section_name):
    """
    Extract questions from a section dynamically.

    Supports:
    - section directly containing a list
    - section containing a 'questions' list
    """

    if isinstance(section_data, list):
        questions = section_data

    elif isinstance(section_data, dict) and "questions" in section_data:
        questions = section_data["questions"]

    else:
        raise PaperValidationError(
            f"Section '{section_name}' must contain a question list."
        )

    if not isinstance(questions, list):
        raise PaperValidationError(
            f"Questions in section '{section_name}' must be a list."
        )

    return questions


def validate_paper(blueprint, selected_questions_data):
    """
    Dynamically validates selected questions against a blueprint.

    No subject, unit, section, mark, RUA, difficulty, or CO values
    are hardcoded.

    Returns:
        {
            "valid": bool,
            "errors": [...],
            "summary": {...}
        }
    """

    if not isinstance(blueprint, dict):
        raise PaperValidationError("Blueprint must be a dictionary.")

    required_blueprint_keys = [
        "paper_information",
        "requirements",
        "question_pattern",
        "calculated_values"
    ]

    for key in required_blueprint_keys:
        if key not in blueprint:
            raise PaperValidationError(
                f"Blueprint is missing required key '{key}'."
            )

    requirements = blueprint["requirements"]
    question_pattern = blueprint["question_pattern"]
    calculated_values = blueprint["calculated_values"]

    if not isinstance(requirements, dict):
        raise PaperValidationError(
            "'requirements' must be a dictionary."
        )

    if not isinstance(question_pattern, dict):
        raise PaperValidationError(
            "'question_pattern' must be a dictionary."
        )

    errors = []

    try:
        selected_sections = _get_question_sections(
            selected_questions_data
        )
    except PaperValidationError as error:
        return {
            "valid": False,
            "errors": [str(error)],
            "summary": {}
        }

    # ---------------------------------------------------------
    # 1. Validate sections dynamically against question pattern
    # ---------------------------------------------------------

    expected_sections = set(question_pattern.keys())
    actual_sections = set(selected_sections.keys())

    missing_sections = expected_sections - actual_sections
    unexpected_sections = actual_sections - expected_sections

    for section_name in sorted(missing_sections):
        errors.append(
            f"Missing required section '{section_name}'."
        )

    for section_name in sorted(unexpected_sections):
        errors.append(
            f"Unexpected section '{section_name}' found."
        )

    all_questions = []

    for section_name, pattern_details in question_pattern.items():

        if section_name not in selected_sections:
            continue

        try:
            questions = _extract_questions(
                selected_sections[section_name],
                section_name
            )
        except PaperValidationError as error:
            errors.append(str(error))
            continue

        expected_count = pattern_details.get(
            "questions_to_generate"
        )

        expected_marks = pattern_details.get(
            "marks_per_question"
        )

        if expected_count is None:
            errors.append(
                f"Blueprint section '{section_name}' is missing "
                "'questions_to_generate'."
            )
        elif len(questions) != expected_count:
            errors.append(
                f"Section '{section_name}' contains "
                f"{len(questions)} questions but blueprint requires "
                f"{expected_count}."
            )

        for index, question in enumerate(questions, start=1):

            if not isinstance(question, dict):
                errors.append(
                    f"Question {index} in section '{section_name}' "
                    "must be a dictionary."
                )
                continue

            question_copy = dict(question)
            question_copy["_section"] = section_name
            all_questions.append(question_copy)

            if expected_marks is not None:
                actual_marks = question.get("marks")

                if actual_marks != expected_marks:
                    errors.append(
                        f"Question {index} in section '{section_name}' "
                        f"has {actual_marks} marks but requires "
                        f"{expected_marks}."
                    )

    # ---------------------------------------------------------
    # 2. Validate total generated question count
    # ---------------------------------------------------------

    expected_question_count = calculated_values.get(
        "total_questions_to_generate"
    )

    actual_question_count = len(all_questions)

    if (
        expected_question_count is not None
        and actual_question_count != expected_question_count
    ):
        errors.append(
            f"Total selected questions is {actual_question_count} "
            f"but blueprint requires {expected_question_count}."
        )

    # ---------------------------------------------------------
    # 3. Validate generated marks
    # ---------------------------------------------------------

    expected_generated_marks = calculated_values.get(
        "generated_question_marks"
    )

    actual_generated_marks = sum(
        question.get("marks", 0)
        for question in all_questions
        if isinstance(question.get("marks", 0), (int, float))
    )

    if (
        expected_generated_marks is not None
        and actual_generated_marks != expected_generated_marks
    ):
        errors.append(
            f"Total generated question marks is "
            f"{actual_generated_marks} but blueprint requires "
            f"{expected_generated_marks}."
        )

    # ---------------------------------------------------------
    # 4. Validate attempted marks from dynamic question pattern
    # ---------------------------------------------------------

    expected_attempted_marks = sum(
        details.get("questions_to_attempt", 0)
        * details.get("marks_per_question", 0)
        for details in question_pattern.values()
        if isinstance(details, dict)
    )

    blueprint_attempted_marks = calculated_values.get(
        "total_attempted_marks"
    )

    if (
        blueprint_attempted_marks is not None
        and expected_attempted_marks != blueprint_attempted_marks
    ):
        errors.append(
            "Blueprint attempted marks are internally inconsistent: "
            f"pattern calculates {expected_attempted_marks} but "
            f"calculated_values contains {blueprint_attempted_marks}."
        )

    # ---------------------------------------------------------
    # 5. Validate canonical ID uniqueness
    # ---------------------------------------------------------

    canonical_ids = []

    for question in all_questions:

        canonical_id = question.get("canonical_id")

        if canonical_id is None:
            errors.append(
                f"Question in section '{question['_section']}' "
                "is missing 'canonical_id'."
            )
        else:
            canonical_ids.append(canonical_id)

    duplicate_canonical_ids = [
        canonical_id
        for canonical_id, count in Counter(canonical_ids).items()
        if count > 1
    ]

    for canonical_id in sorted(
        duplicate_canonical_ids,
        key=str
    ):
        errors.append(
            f"Duplicate canonical_id found: '{canonical_id}'."
        )

    # ---------------------------------------------------------
    # 6. Validate RUA allocation dynamically
    # ---------------------------------------------------------

    expected_rua_allocation = requirements.get(
        "rua_allocation",
        {}
    )

    if not isinstance(expected_rua_allocation, dict):
        errors.append(
            "Blueprint 'rua_allocation' must be a dictionary."
        )
        expected_rua_allocation = {}

    actual_rua = defaultdict(float)

    for question in all_questions:

        rua = question.get("rua")
        marks = question.get("marks")

        if rua is None:
            errors.append(
                f"Question in section '{question['_section']}' "
                "is missing 'rua'."
            )
            continue

        if not isinstance(marks, (int, float)):
            errors.append(
                f"Question in section '{question['_section']}' "
                "has invalid 'marks'."
            )
            continue

        actual_rua[rua] += marks

    expected_rua = defaultdict(float)

    for unit, allocation in expected_rua_allocation.items():

        if not isinstance(allocation, dict):
            errors.append(
                f"RUA allocation for '{unit}' must be a dictionary."
            )
            continue

        for rua_name, value in allocation.items():

            if rua_name == "Total":
                continue

            if isinstance(value, (int, float)):
                expected_rua[rua_name] += value

    all_rua_categories = set(expected_rua.keys()) | set(
        actual_rua.keys()
    )

    for rua_name in sorted(all_rua_categories, key=str):

        expected_value = expected_rua[rua_name]
        actual_value = actual_rua[rua_name]

        if actual_value != expected_value:
            errors.append(
                f"RUA '{rua_name}' has {actual_value} selected marks "
                f"but requires {expected_value}."
            )

    # ---------------------------------------------------------
    # 7. Validate difficulty allocation dynamically
    # ---------------------------------------------------------

    expected_difficulty = requirements.get(
        "difficulty_allocation",
        {}
    )

    if not isinstance(expected_difficulty, dict):
        errors.append(
            "Blueprint 'difficulty_allocation' must be a dictionary."
        )
        expected_difficulty = {}

    actual_difficulty = defaultdict(float)

    for question in all_questions:

        difficulty = question.get("difficulty")
        marks = question.get("marks")

        if difficulty is None:
            errors.append(
                f"Question in section '{question['_section']}' "
                "is missing 'difficulty'."
            )
            continue

        if isinstance(marks, (int, float)):
            actual_difficulty[difficulty] += marks

    all_difficulty_levels = (
        set(expected_difficulty.keys())
        | set(actual_difficulty.keys())
    )

    for difficulty in sorted(
        all_difficulty_levels,
        key=str
    ):

        expected_value = expected_difficulty.get(
            difficulty,
            0
        )

        actual_value = actual_difficulty[difficulty]

        if actual_value != expected_value:
            errors.append(
                f"Difficulty '{difficulty}' has "
                f"{actual_value} selected marks but requires "
                f"{expected_value}."
            )

    # ---------------------------------------------------------
    # 8. Validate CO coverage dynamically
    # ---------------------------------------------------------

    required_cos = requirements.get(
        "co_requirements",
        []
    )

    if not isinstance(required_cos, list):
        errors.append(
            "Blueprint 'co_requirements' must be a list."
        )
        required_cos = []

    actual_cos = {
        question.get("course_outcome")
        for question in all_questions
        if question.get("course_outcome") is not None
    }

    for co in required_cos:

        if co not in actual_cos:
            errors.append(
                f"Required CO '{co}' is not represented "
                "in the selected questions."
            )

    # ---------------------------------------------------------
    # 9. Validate selected units dynamically
    # ---------------------------------------------------------

    selected_units = requirements.get(
        "selected_units",
        []
    )

    if not isinstance(selected_units, list):
        errors.append(
            "Blueprint 'selected_units' must be a list."
        )
        selected_units = []

    for question in all_questions:

        unit = question.get("unit")

        if unit is None:
            errors.append(
                f"Question in section '{question['_section']}' "
                "is missing 'unit'."
            )

        elif selected_units and unit not in selected_units:
            errors.append(
                f"Question with canonical_id "
                f"'{question.get('canonical_id')}' belongs to "
                f"unselected unit '{unit}'."
            )

    # ---------------------------------------------------------
    # Return structured result
    # ---------------------------------------------------------

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "summary": {
            "total_questions": actual_question_count,
            "generated_question_marks": actual_generated_marks,
            "attempted_question_marks": expected_attempted_marks,
            "unique_canonical_ids": len(set(canonical_ids)),
            "rua_marks": dict(actual_rua),
            "difficulty_marks": dict(actual_difficulty),
            "covered_cos": sorted(
                actual_cos,
                key=str
            )
        }
    }


def _unique_docx_path(selected_questions_path, output_dir=FORMATTER_OUTPUT):
    """Build a unique formatter output path without replacing an earlier DOCX."""
    safe_stem = re.sub(r"[^A-Za-z0-9_-]+", "_", selected_questions_path.stem).strip("_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = output_dir / f"question_paper_{safe_stem}_{timestamp}.docx"
    candidate = base
    suffix = 1
    while candidate.exists():
        candidate = output_dir / f"question_paper_{safe_stem}_{timestamp}_{suffix}.docx"
        suffix += 1
    return candidate


def main():
    """Validate the newest selected-questions file, then format it if valid."""
    selected_path = find_latest_selected_questions()
    if selected_path is None:
        print(f"No selected_questions*.json files found in {VALIDATOR_SAMPLE_DATA}")
        return 1

    print(f"Selected questions: {selected_path}")
    try:
        with selected_path.open(encoding="utf-8") as handle:
            selected_questions = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read selected questions JSON: {exc}")
        return 1

    if not isinstance(selected_questions, dict):
        print("Selected questions JSON must contain an object at its root.")
        return 1

    blueprint_candidates = find_blueprints_for(selected_questions)
    if not blueprint_candidates:
        info = selected_questions.get("paper_information", {})
        identity = info.get("subject_code") or info.get("subject") or "unknown subject"
        print(f"No matching Blueprint found for {identity}.")
        print("Searched: " + ", ".join(str(path) for path in BLUEPRINT_DIRECTORIES))
        return 1

    # Prefer the newest matching Blueprint that validates the complete paper.
    # If none validate, report errors from the newest matching Blueprint.
    chosen_path, chosen_blueprint = blueprint_candidates[0]
    chosen_result = None
    for blueprint_path, blueprint in blueprint_candidates:
        result = validate_paper(blueprint, selected_questions)
        if result["valid"]:
            chosen_path, chosen_blueprint, chosen_result = blueprint_path, blueprint, result
            break
    if chosen_result is None:
        chosen_result = validate_paper(chosen_blueprint, selected_questions)

    print(f"Blueprint: {chosen_path}")
    if not chosen_result["valid"]:
        print("Paper validation failed; DOCX was not generated:")
        for error in chosen_result["errors"]:
            print(f"- {error}")
        return 1

    print("Paper validation passed.")
    print(
        "Summary: "
        f"{chosen_result['summary']['total_questions']} questions, "
        f"{chosen_result['summary']['generated_question_marks']} generated marks."
    )

    # Import the existing formatter only after the paper passes validation.
    formatter_path = str(FORMATTER_ROOT)
    if formatter_path not in sys.path:
        sys.path.insert(0, formatter_path)
    try:
        from paper_formatter import validate_and_format_paper
        from docx_generator import generate_docx
    except ImportError as exc:
        print(f"Could not load Question_Paper_Formatter modules: {exc}")
        return 1

    format_valid, format_errors, formatted_paper = validate_and_format_paper(
        selected_questions,
        blueprint=chosen_blueprint,
    )
    if not format_valid:
        print("Formatter validation failed; DOCX was not generated:")
        for error in format_errors:
            print(f"- {error}")
        return 1

    FORMATTER_OUTPUT.mkdir(parents=True, exist_ok=True)
    output_path = _unique_docx_path(selected_path)
    try:
        generate_docx(formatted_paper, str(output_path))
    except Exception as exc:
        print(f"DOCX generation failed: {exc}")
        return 1

    print(f"DOCX saved: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
