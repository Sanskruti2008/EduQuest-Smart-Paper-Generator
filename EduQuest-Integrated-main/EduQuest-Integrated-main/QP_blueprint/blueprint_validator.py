def validate_blueprint(blueprint):

    errors = []

    # =========================
    # 1. Check paper information
    # =========================

    paper_info = blueprint.get("paper_information")

    if not isinstance(paper_info, dict):
        errors.append("Missing or invalid paper_information section")

    else:
        required_fields = [
            "branch",
            "semester",
            "subject",
            "subject_code",
            "exam_type",
            "paper_total_marks"
        ]

        for field in required_fields:
            if field not in paper_info:
                errors.append(
                    f"Missing paper_information field: {field}"
                )

        paper_total_marks = paper_info.get(
            "paper_total_marks"
        )

        if not isinstance(
            paper_total_marks,
            (int, float)
        ) or isinstance(paper_total_marks, bool):
            errors.append(
                "paper_total_marks must be a number"
            )

        elif paper_total_marks <= 0:
            errors.append(
                "paper_total_marks must be greater than 0"
            )

    # =========================
    # 2. Check requirements
    # =========================

    requirements = blueprint.get("requirements")

    if not isinstance(requirements, dict):
        errors.append("Missing or invalid requirements section")

    else:

        selected_units = requirements.get("selected_units")

        if not isinstance(selected_units, list) or not selected_units:
            errors.append(
                "At least one unit must be selected"
            )

        co_requirements = requirements.get(
            "co_requirements"
        )

        if (
            not isinstance(co_requirements, list)
            or not co_requirements
        ):
            errors.append(
                "At least one CO requirement must be provided"
            )

        # -------------------------
        # Difficulty allocation
        # -------------------------
        difficulty = requirements.get(
            "difficulty_allocation"
        )

        if not isinstance(difficulty, dict):
            errors.append(
                "difficulty_allocation must be an object"
            )

        else:

            required_difficulties = [
                "Easy",
                "Medium",
                "Hard"
            ]

            for level in required_difficulties:

                if level not in difficulty:
                    errors.append(
                        f"Missing difficulty level: {level}"
                    )

                elif not isinstance(
                    difficulty[level],
                    (int, float)
                ) or isinstance(difficulty[level], bool):
                    errors.append(
                        f"{level} difficulty value must be a number"
                    )

                elif difficulty[level] < 0:
                    errors.append(
                        f"{level} difficulty value cannot be negative"
                    )

            if all(
                level in difficulty
                and isinstance(
                    difficulty[level],
                    (int, float)
                )
                and not isinstance(difficulty[level], bool)
                for level in required_difficulties
            ):

                difficulty_total = sum(
                    difficulty[level]
                    for level in required_difficulties
                )

                # After scaling, difficulty_allocation reflects generated question marks,
                # not attempted (paper_total_marks). Validate against generated_question_marks
                # from calculated_values; fall back to paper_total_marks if not yet available.
                generated_marks = blueprint.get(
                    "calculated_values", {}
                ).get("generated_question_marks")

                reference = (
                    generated_marks
                    if isinstance(generated_marks, (int, float)) and not isinstance(generated_marks, bool)
                    else blueprint.get("paper_information", {}).get("paper_total_marks")
                )

                if (
                    isinstance(reference, (int, float))
                    and not isinstance(reference, bool)
                    and difficulty_total != reference
                ):
                    errors.append(
                        f"Difficulty allocation total is "
                        f"{difficulty_total}, but generated question "
                        f"marks is {reference}"
                    )

        # -------------------------
        # RUA allocation
        # -------------------------
        rua_allocation = requirements.get("rua_allocation")

        if not isinstance(rua_allocation, dict):
            errors.append("rua_allocation must be an object")
        elif not rua_allocation:
            errors.append("rua_allocation cannot be empty")
        else:
            if isinstance(selected_units, list) and selected_units:
                for unit in selected_units:
                    if unit not in rua_allocation:
                        errors.append(
                            f"Unit '{unit}' present in selected_units is missing from rua_allocation"
                        )
                selected_units_set = set(selected_units)
                for unit in rua_allocation:
                    if unit not in selected_units_set:
                        errors.append(
                            f"Unit '{unit}' in rua_allocation is not present in selected_units"
                        )

            generated_marks = blueprint.get(
                "calculated_values", {}
            ).get("generated_question_marks")

            reference = (
                generated_marks
                if isinstance(generated_marks, (int, float)) and not isinstance(generated_marks, bool)
                else blueprint.get("paper_information", {}).get("paper_total_marks")
            )

            rua_grand_total = 0
            all_rua_valid = True

            for unit, details in rua_allocation.items():
                if not isinstance(details, dict):
                    errors.append(
                        f"RUA allocation for unit '{unit}' must be an object"
                    )
                    all_rua_valid = False
                    continue

                unit_components_valid = True
                for comp in ["R", "U", "A"]:
                    if comp not in details:
                        errors.append(
                            f"Unit '{unit}' is missing component '{comp}' in rua_allocation"
                        )
                        unit_components_valid = False
                        all_rua_valid = False
                    elif not isinstance(details[comp], (int, float)) or isinstance(details[comp], bool):
                        errors.append(
                            f"Unit '{unit}' component '{comp}' must be a number"
                        )
                        unit_components_valid = False
                        all_rua_valid = False
                    elif details[comp] < 0:
                        errors.append(
                            f"Unit '{unit}' component '{comp}' cannot be negative"
                        )
                        unit_components_valid = False
                        all_rua_valid = False
                    elif details[comp] % 2 != 0:
                        errors.append(
                            f"Unit '{unit}' component '{comp}' must be an even number (got {details[comp]})"
                        )
                        unit_components_valid = False
                        all_rua_valid = False

                if unit_components_valid:
                    unit_comp_sum = details["R"] + details["U"] + details["A"]
                    if "Total" in details:
                        tot = details["Total"]
                        if not isinstance(tot, (int, float)) or isinstance(tot, bool):
                            errors.append(
                                f"Unit '{unit}' Total must be a number"
                            )
                            all_rua_valid = False
                        elif tot != unit_comp_sum:
                            errors.append(
                                f"Unit '{unit}' R ({details['R']}) + U ({details['U']}) + A ({details['A']}) "
                                f"must equal Total ({tot})"
                            )
                            all_rua_valid = False
                        elif tot % 2 != 0:
                            errors.append(
                                f"Unit '{unit}' Total must be an even number (got {tot})"
                            )
                            all_rua_valid = False
                    rua_grand_total += unit_comp_sum

            if all_rua_valid and isinstance(reference, (int, float)) and not isinstance(reference, bool):
                if rua_grand_total != reference:
                    errors.append(
                        f"RUA allocation grand total is {rua_grand_total}, "
                        f"but generated question marks is {reference}"
                    )

    # =========================
    # 3. Check question pattern
    # =========================

    question_pattern = blueprint.get("question_pattern")

    if not isinstance(question_pattern, dict):

        errors.append(
            "Missing or invalid question_pattern section"
        )

    elif not question_pattern:

        errors.append(
            "Question pattern cannot be empty"
        )

    else:

        calculated_generated_questions = 0
        calculated_generated_marks = 0
        calculated_attempted_marks = 0

        for question_number, details in question_pattern.items():

            if not isinstance(details, dict):
                errors.append(
                    f"{question_number} must be an object"
                )
                continue

            required_fields = [
                "questions_to_generate",
                "questions_to_attempt",
                "marks_per_question",
                "generated_section_marks",
                "attempted_section_marks"
            ]

            for field in required_fields:

                if field not in details:
                    errors.append(
                        f"{question_number} is missing {field}"
                    )

            if not all(
                field in details
                for field in required_fields
            ):
                continue

            questions_to_generate = details[
                "questions_to_generate"
            ]

            questions_to_attempt = details[
                "questions_to_attempt"
            ]

            marks_per_question = details[
                "marks_per_question"
            ]

            generated_section_marks = details[
                "generated_section_marks"
            ]

            attempted_section_marks = details[
                "attempted_section_marks"
            ]

            numeric_values = [
                questions_to_generate,
                questions_to_attempt,
                marks_per_question,
                generated_section_marks,
                attempted_section_marks
            ]

            if not all(
                isinstance(value, (int, float)) and not isinstance(value, bool)
                for value in numeric_values
            ):
                errors.append(
                    f"{question_number} contains non-numeric values"
                )
                continue

            if questions_to_generate <= 0:
                errors.append(
                    f"{question_number}: questions_to_generate "
                    f"must be greater than 0"
                )

            if questions_to_attempt <= 0:
                errors.append(
                    f"{question_number}: questions_to_attempt "
                    f"must be greater than 0"
                )

            if marks_per_question <= 0:
                errors.append(
                    f"{question_number}: marks_per_question "
                    f"must be greater than 0"
                )

            # Internal choice validation
            if (
                questions_to_attempt
                > questions_to_generate
            ):
                errors.append(
                    f"{question_number}: questions_to_attempt "
                    f"cannot be greater than "
                    f"questions_to_generate"
                )

            expected_generated_marks = (
                questions_to_generate
                * marks_per_question
            )

            expected_attempted_marks = (
                questions_to_attempt
                * marks_per_question
            )

            if (
                generated_section_marks
                != expected_generated_marks
            ):
                errors.append(
                    f"{question_number}: incorrect "
                    f"generated_section_marks. "
                    f"Expected {expected_generated_marks}, "
                    f"got {generated_section_marks}"
                )

            if (
                attempted_section_marks
                != expected_attempted_marks
            ):
                errors.append(
                    f"{question_number}: incorrect "
                    f"attempted_section_marks. "
                    f"Expected {expected_attempted_marks}, "
                    f"got {attempted_section_marks}"
                )

            calculated_generated_questions += (
                questions_to_generate
            )

            calculated_generated_marks += (
                generated_section_marks
            )

            calculated_attempted_marks += (
                attempted_section_marks
            )

    # =========================
    # 4. Check calculated values
    # =========================

    calculated_values = blueprint.get(
        "calculated_values"
    )

    if not isinstance(calculated_values, dict):

        errors.append(
            "Missing or invalid calculated_values section"
        )

    else:

        saved_total_questions = calculated_values.get(
            "total_questions_to_generate"
        )

        saved_generated_marks = calculated_values.get(
            "generated_question_marks"
        )

        saved_attempted_marks = calculated_values.get(
            "total_attempted_marks"
        )

        if (
            saved_total_questions
            != calculated_generated_questions
        ):
            errors.append(
                f"Incorrect total_questions_to_generate. "
                f"Expected {calculated_generated_questions}, "
                f"got {saved_total_questions}"
            )

        if (
            saved_generated_marks
            != calculated_generated_marks
        ):
            errors.append(
                f"Incorrect generated_question_marks. "
                f"Expected {calculated_generated_marks}, "
                f"got {saved_generated_marks}"
            )

        if (
            saved_attempted_marks
            != calculated_attempted_marks
        ):
            errors.append(
                f"Incorrect total_attempted_marks. "
                f"Expected {calculated_attempted_marks}, "
                f"got {saved_attempted_marks}"
            )

    # =========================
    # 5. Final paper marks check
    # =========================

    paper_total_marks = blueprint.get(
        "paper_information",
        {}
    ).get("paper_total_marks")

    if (
        isinstance(paper_total_marks, (int, float))
        and not isinstance(paper_total_marks, bool)
        and isinstance(calculated_values, dict)
        and saved_attempted_marks != paper_total_marks
    ):
        errors.append(
            f"Total attempted marks are {saved_attempted_marks}, "
            f"but paper total marks are {paper_total_marks}"
        )

    # =========================
    # Final result
    # =========================

    if errors:
        return {
            "valid": False,
            "errors": errors
        }

    return {
        "valid": True,
        "errors": []
    }