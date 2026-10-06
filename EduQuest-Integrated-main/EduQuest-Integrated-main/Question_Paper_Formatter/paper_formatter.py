import json
import os


def validate_and_format_paper(raw_data, blueprint=None):
    """
    Validates the structure of raw_data (selected questions JSON) and formats it
    into a structured question paper object.

    Args:
        raw_data (dict): Loaded from selected_questions.json.
        blueprint (dict | None): The blueprint produced by QP_blueprint.
            When supplied, instructions are read from blueprint["instructions"]
            and each section's title is read from
            blueprint["question_pattern"][section_name]["title"].
            When None, the formatter falls back to reading instructions and
            titles from raw_data itself (backward-compatible path).

    Returns:
        tuple: (is_valid, errors, formatted_paper)
    """
    errors = []

    # ------------------------------------------------------------------
    # 1. Validate basic raw_data structure
    # ------------------------------------------------------------------
    if not isinstance(raw_data, dict):
        errors.append("Invalid input data format: Expected a JSON object (dictionary).")
        return False, errors, None

    if "paper_information" not in raw_data:
        errors.append("Missing required root field: 'paper_information'.")
    elif not isinstance(raw_data["paper_information"], dict):
        errors.append("'paper_information' must be a JSON object (dictionary).")

    if "sections" not in raw_data:
        errors.append("Missing required root field: 'sections'.")
    elif not isinstance(raw_data["sections"], dict):
        errors.append("'sections' must be a JSON object (dictionary).")
    elif not raw_data["sections"]:
        errors.append("'sections' must contain at least one question section.")

    if errors:
        return False, errors, None

    raw_info = raw_data["paper_information"]
    raw_sections = raw_data["sections"]

    # ------------------------------------------------------------------
    # 2. Instructions — blueprint is the source of truth
    #    Fallback: read from raw_data for backward compatibility
    # ------------------------------------------------------------------
    if blueprint is not None and isinstance(blueprint, dict):
        raw_instructions = blueprint.get("instructions") or []
    else:
        raw_instructions = raw_data.get("instructions")
        if raw_instructions is None:
            raw_instructions = raw_info.get("instructions")

    formatted_instructions = []
    if raw_instructions is not None:
        if isinstance(raw_instructions, list):
            for inst in raw_instructions:
                if isinstance(inst, str) and inst.strip():
                    formatted_instructions.append(inst.strip())
                elif not isinstance(inst, str):
                    errors.append(
                        f"Instruction item must be a string, got: {type(inst).__name__}"
                    )
        elif isinstance(raw_instructions, str):
            for line in raw_instructions.splitlines():
                if line.strip():
                    formatted_instructions.append(line.strip())
        else:
            errors.append("'instructions' must be a list of strings or a multiline string.")

    # ------------------------------------------------------------------
    # 3. Blueprint question_pattern — used for per-section titles
    # ------------------------------------------------------------------
    bp_pattern = {}
    if blueprint is not None and isinstance(blueprint, dict):
        bp_pattern = blueprint.get("question_pattern") or {}
        if not isinstance(bp_pattern, dict):
            bp_pattern = {}

    # ------------------------------------------------------------------
    # 4. Format paper_information
    # ------------------------------------------------------------------
    formatted_info = {
        "branch": raw_info.get("branch", "N/A"),
        "semester": raw_info.get("semester", "N/A"),
        "subject": raw_info.get("subject", "N/A"),
        "subject_code": str(raw_info.get("subject_code", "N/A")),
        "exam_type": raw_info.get("exam_type", "N/A"),
        "paper_total_marks": raw_info.get("paper_total_marks", 0),
    }

    if not isinstance(formatted_info["paper_total_marks"], (int, float)):
        errors.append("'paper_total_marks' in paper_information must be a number.")

    # ------------------------------------------------------------------
    # 5. Process sections
    # ------------------------------------------------------------------
    formatted_sections = {}
    total_generated_questions = 0
    total_generated_marks = 0

    number_words = {
        1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR", 5: "FIVE",
        6: "SIX", 7: "SEVEN", 8: "EIGHT", 9: "NINE", 10: "TEN",
        11: "ELEVEN", 12: "TWELVE",
    }

    for sec_name, sec_data in raw_sections.items():
        if not isinstance(sec_data, dict):
            errors.append(f"Section '{sec_name}' must be a JSON object (dictionary).")
            continue

        if "questions" not in sec_data:
            errors.append(f"Section '{sec_name}' is missing 'questions' field.")
            continue

        questions_list = sec_data["questions"]
        if not isinstance(questions_list, list):
            errors.append(f"'questions' field in Section '{sec_name}' must be a list.")
            continue

        if not questions_list:
            errors.append(f"Section '{sec_name}' has an empty questions list.")
            continue

        formatted_questions = []
        section_total_marks = 0

        for idx, q_data in enumerate(questions_list):
            q_num = idx + 1
            if not isinstance(q_data, dict):
                errors.append(
                    f"Question {q_num} in section '{sec_name}' must be a JSON object."
                )
                continue

            q_text = q_data.get("question_text")
            if not q_text:
                errors.append(
                    f"Question {q_num} in section '{sec_name}' is missing 'question_text'."
                )
            elif not isinstance(q_text, str) or not q_text.strip():
                errors.append(
                    f"Question {q_num} in section '{sec_name}' must have non-empty "
                    "string for 'question_text'."
                )

            marks = q_data.get("marks")
            if marks is None:
                errors.append(
                    f"Question {q_num} in section '{sec_name}' is missing 'marks'."
                )
            elif not isinstance(marks, (int, float)):
                errors.append(
                    f"Question {q_num} in section '{sec_name}' has invalid marks type: "
                    f"'{type(marks).__name__}'. Marks must be a number."
                )
            elif marks <= 0:
                errors.append(
                    f"Question {q_num} in section '{sec_name}' has invalid marks value: "
                    f"{marks}. Marks must be positive."
                )
            else:
                section_total_marks += marks

            co = q_data.get("course_outcome") or q_data.get("co")
            formatted_q = {
                "canonical_id": q_data.get("canonical_id"),
                "question_text": q_text,
                "unit": q_data.get("unit"),
                "marks": marks,
                "rua": q_data.get("rua"),
                "difficulty": q_data.get("difficulty"),
                "course_outcome": co,
            }
            formatted_questions.append(formatted_q)

        # ---- Section label --------------------------------------------------
        custom_label = sec_data.get("section_label") or sec_data.get("section_number")
        if custom_label:
            section_label = str(custom_label).strip()
        else:
            import re
            m = re.match(r"^[Qq]\.?(\d+)$", sec_name.strip())
            if m:
                section_label = f"Q. {m.group(1)}"
            else:
                section_label = sec_name.strip()

        # ---- Section title --------------------------------------------------
        # Priority:
        #   1. blueprint["question_pattern"][sec_name]["title"]  (source of truth)
        #   2. sec_data["title"] / ["section_title"] / ["attempt_instruction"]
        #      (backward-compatible: works when no blueprint is provided)
        #   3. Derive from questions_to_attempt (last resort fallback)
        bp_sec = bp_pattern.get(sec_name, {})
        bp_title = bp_sec.get("title", "") if isinstance(bp_sec, dict) else ""

        if bp_title:
            section_title = bp_title.strip()
        else:
            inline_title = (
                sec_data.get("title")
                or sec_data.get("section_title")
                or sec_data.get("attempt_instruction")
            )
            q_attempt = sec_data.get("questions_to_attempt")
            if inline_title:
                section_title = str(inline_title).strip()
            elif isinstance(q_attempt, int) and q_attempt > 0:
                if q_attempt < len(formatted_questions):
                    word = number_words.get(q_attempt, str(q_attempt))
                    section_title = f"Attempt any {word}"
                else:
                    section_title = "Attempt all questions"
            else:
                section_title = ""

        # ---- Attempted marks ------------------------------------------------
        q_attempt = sec_data.get("questions_to_attempt")
        attempted_marks = sec_data.get("attempted_section_marks") or sec_data.get("section_marks")
        if attempted_marks is None:
            if isinstance(q_attempt, int) and q_attempt > 0 and formatted_questions:
                first_marks = formatted_questions[0]["marks"] or 0
                attempted_marks = q_attempt * first_marks
            else:
                attempted_marks = section_total_marks

        formatted_sections[sec_name] = {
            "section_label": section_label,
            "title": section_title,
            "attempted_marks": attempted_marks,
            "questions_to_attempt": q_attempt,
            "questions": formatted_questions,
            "section_total_marks": section_total_marks,
            "num_questions": len(formatted_questions),
        }

        total_generated_questions += len(formatted_questions)
        total_generated_marks += section_total_marks

    # ------------------------------------------------------------------
    # 6. Final validity check
    # ------------------------------------------------------------------
    if errors:
        return False, errors, None

    formatted_paper = {
        "instructions": formatted_instructions,
        "paper_information": formatted_info,
        "sections": formatted_sections,
        "total_generated_questions": total_generated_questions,
        "total_generated_marks": total_generated_marks,
    }

    return True, [], formatted_paper


def load_json_file(file_path):
    """
    Safely loads a JSON file.

    Returns:
        tuple: (success, data_or_error_message)
    """
    if not os.path.exists(file_path):
        return False, f"File not found at: {file_path}"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return True, data
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON syntax in file '{file_path}': {str(e)}"
    except Exception as e:
        return False, f"Error reading file '{file_path}': {str(e)}"
