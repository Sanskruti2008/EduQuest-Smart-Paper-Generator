def validate_faculty_input(faculty_data):
    """
    Validates faculty input data dynamically based on the 32 system requirements.
    Returns:
        dict: {
            "valid": bool,
            "errors": list of str
        }
    """
    errors = []

    # ==========================================
    # Helper to check if a value is a number (int or float) and not boolean
    # ==========================================
    def is_number(val):
        return isinstance(val, (int, float)) and not isinstance(val, bool)

    # ==========================================
    # Helper to check if a value is a positive integer
    # ==========================================
    def is_positive_integer(val):
        return isinstance(val, int) and not isinstance(val, bool) and val > 0

    # ==========================================
    # Helper to check if a value is a positive number
    # ==========================================
    def is_positive_number(val):
        return is_number(val) and val > 0

    # ==========================================
    # Helper to check if a value is a non-negative number
    # ==========================================
    def is_non_negative_number(val):
        return is_number(val) and val >= 0

    # ==========================================
    # 31 & 32. Safely handle input not being a dictionary
    # ==========================================
    if not isinstance(faculty_data, dict):
        return {
            "valid": False,
            "errors": ["Faculty input data must be a dictionary."]
        }

    # ==========================================
    # 1. Required top-level fields check
    # ==========================================
    required_fields = [
        "branch", "semester", "subject", "subject_code", "exam_type", 
        "total_marks", "selected_units", "difficulty_allocation", 
        "rua_allocation", "co_requirements", "question_pattern"
    ]
    
    missing_fields = [field for field in required_fields if field not in faculty_data]
    if missing_fields:
        errors.append(f"Missing required top-level fields: {', '.join(missing_fields)}")
        # We return early if we cannot even access core structures safely
        return {
            "valid": False,
            "errors": errors
        }

    branch = faculty_data.get("branch")
    semester = faculty_data.get("semester")
    subject = faculty_data.get("subject")
    subject_code = faculty_data.get("subject_code")
    exam_type = faculty_data.get("exam_type")
    total_marks = faculty_data.get("total_marks")
    selected_units = faculty_data.get("selected_units")
    difficulty_allocation = faculty_data.get("difficulty_allocation")
    rua_allocation = faculty_data.get("rua_allocation")
    co_requirements = faculty_data.get("co_requirements")
    question_pattern = faculty_data.get("question_pattern")

    # R/U/A and difficulty describe the full generated pool, including
    # internal-choice questions. The question pattern separately validates
    # the marks a student attempts.
    generated_pool_marks = None
    if isinstance(question_pattern, dict):
        generated_pool_marks = 0
        for section in question_pattern.values():
            if isinstance(section, dict):
                generated_pool_marks += (
                    section.get("questions_to_generate", 0)
                    * section.get("marks_per_question", 0)
                    if is_number(section.get("questions_to_generate", 0))
                    and is_number(section.get("marks_per_question", 0))
                    else 0
                )

    # ==========================================
    # 2. String fields check (branch, subject, subject_code, exam_type)
    # ==========================================
    for field_name, value in [("branch", branch), ("subject", subject), 
                              ("subject_code", subject_code), ("exam_type", exam_type)]:
        if not isinstance(value, str):
            errors.append(f"'{field_name}' must be a string.")
        elif not value.strip():
            errors.append(f"'{field_name}' must be a non-empty string.")

    # ==========================================
    # 3. Semester check
    # ==========================================
    if semester is not None:
        if not is_positive_integer(semester):
            errors.append("semester must be a positive integer.")
    else:
        errors.append("semester cannot be null/missing.")

    # ==========================================
    # 4. Total marks check
    # ==========================================
    if total_marks is not None:
        if not is_positive_number(total_marks):
            errors.append("total_marks must be a positive number.")
    else:
        errors.append("total_marks cannot be null/missing.")

    # ==========================================
    # 5 & 6. Selected units check
    # ==========================================
    if not isinstance(selected_units, list):
        errors.append("selected_units must be a list.")
    elif not selected_units:
        errors.append("selected_units must be a non-empty list.")
    else:
        # Check for duplicates in selected_units
        seen_units = set()
        has_duplicates = False
        for unit in selected_units:
            if unit in seen_units:
                has_duplicates = True
            seen_units.add(unit)
        if has_duplicates:
            errors.append("selected_units cannot contain duplicate values.")

    # ==========================================
    # 7. RUA Allocation structure check
    # ==========================================
    if not isinstance(rua_allocation, dict):
        errors.append("rua_allocation must be a dictionary.")
    else:
        # ==========================================
        # 8 & 9. Every selected unit must match rua_allocation and vice versa
        # ==========================================
        if isinstance(selected_units, list):
            # Check selected units match entries in rua_allocation
            for unit in selected_units:
                if unit not in rua_allocation:
                    errors.append(f"Unit '{unit}' present in selected_units is missing from rua_allocation.")
            
            # Check rua_allocation doesn't contain extra units
            selected_units_set = set(selected_units)
            for unit in rua_allocation:
                if unit not in selected_units_set:
                    errors.append(f"Unit '{unit}' in rua_allocation is not present in selected_units.")

        # ==========================================
        # 10, 11, 12, 13. RUA Allocation values validation
        # ==========================================
        total_rua_marks_sum = 0
        rua_summing_possible = generated_pool_marks is not None
        
        for unit, details in rua_allocation.items():
            if not isinstance(details, dict):
                errors.append(f"RUA allocation details for unit '{unit}' must be a dictionary.")
                rua_summing_possible = False
                continue

            # 10. Check R, U, A, Total exist
            rua_keys = ["R", "U", "A", "Total"]
            missing_rua_keys = [k for k in rua_keys if k not in details]
            if missing_rua_keys:
                errors.append(f"RUA allocation for unit '{unit}' is missing fields: {', '.join(missing_rua_keys)}")
                rua_summing_possible = False
                continue

            r_val = details.get("R")
            u_val = details.get("U")
            a_val = details.get("A")
            tot_val = details.get("Total")

            # 11. Check R, U, A, and Total are non-negative numbers
            vals_valid = True
            for k, val in [("R", r_val), ("U", u_val), ("A", a_val), ("Total", tot_val)]:
                if not is_non_negative_number(val):
                    errors.append(f"Value '{k}' for unit '{unit}' must be a non-negative number.")
                    vals_valid = False

            if not vals_valid:
                rua_summing_possible = False
                continue

            # 12. Check R + U + A == Total
            if abs((r_val + u_val + a_val) - tot_val) > 1e-9:
                errors.append(f"For unit '{unit}': R ({r_val}) + U ({u_val}) + A ({a_val}) must equal Total ({tot_val}).")
            
            total_rua_marks_sum += tot_val

        # 13. R/U/A must cover the complete generated question pool.
        if rua_summing_possible:
            if abs(total_rua_marks_sum - generated_pool_marks) > 1e-9:
                errors.append(
                    f"Invalid RUA allocation: selected units have a total RUA allocation of {total_rua_marks_sum} marks, "
                    f"but the generated question pool requires {generated_pool_marks} marks."
                )

    # ==========================================
    # 14. Difficulty Allocation structure check
    # ==========================================
    if not isinstance(difficulty_allocation, dict):
        errors.append("difficulty_allocation must be a dictionary.")
    else:
        # 15. Must contain Easy, Medium, Hard
        diff_keys = ["Easy", "Medium", "Hard"]
        missing_diff_keys = [k for k in diff_keys if k not in difficulty_allocation]
        if missing_diff_keys:
            errors.append(f"difficulty_allocation is missing fields: {', '.join(missing_diff_keys)}")
        else:
            easy_val = difficulty_allocation.get("Easy")
            medium_val = difficulty_allocation.get("Medium")
            hard_val = difficulty_allocation.get("Hard")

            # 16. Easy, Medium, Hard must be non-negative numbers
            diff_valid = True
            for k, val in [("Easy", easy_val), ("Medium", medium_val), ("Hard", hard_val)]:
                if not is_non_negative_number(val):
                    errors.append(f"'{k}' difficulty value must be a non-negative number.")
                    diff_valid = False

            # 17. Difficulty must cover the complete generated question pool.
            if diff_valid and generated_pool_marks is not None:
                diff_sum = easy_val + medium_val + hard_val
                if abs(diff_sum - generated_pool_marks) > 1e-9:
                    errors.append(
                        f"Difficulty allocation total is {diff_sum}, "
                        f"but the generated question pool requires {generated_pool_marks} marks."
                    )

    # ==========================================
    # 18 & 19. CO Requirements check
    # ==========================================
    if not isinstance(co_requirements, list):
        errors.append("co_requirements must be a list.")
    elif not co_requirements:
        errors.append("co_requirements must be a non-empty list.")
    else:
        # Check for duplicates in co_requirements
        seen_cos = set()
        has_duplicate_cos = False
        for co in co_requirements:
            if co in seen_cos:
                has_duplicate_cos = True
            seen_cos.add(co)
        if has_duplicate_cos:
            errors.append("co_requirements cannot contain duplicate values.")

    # ==========================================
    # 20. Question Pattern structure check
    # ==========================================
    if not isinstance(question_pattern, dict):
        errors.append("question_pattern must be a dictionary.")
    elif not question_pattern:
        errors.append("question_pattern must be a non-empty dictionary.")
    else:
        # 21. Completely dynamic sections check
        total_attempted_marks = 0
        total_generated_marks = 0
        all_sections_valid = True
        
        for section_name, details in question_pattern.items():
            if not isinstance(details, dict):
                errors.append(f"Question section '{section_name}' details must be a dictionary.")
                all_sections_valid = False
                continue

            # 22. Every section must contain questions_to_generate, questions_to_attempt, marks_per_question
            sec_fields = ["questions_to_generate", "questions_to_attempt", "marks_per_question"]
            missing_sec_fields = [f for f in sec_fields if f not in details]
            if missing_sec_fields:
                errors.append(f"Question section '{section_name}' is missing fields: {', '.join(missing_sec_fields)}")
                all_sections_valid = False
                continue

            gen_qty = details.get("questions_to_generate")
            att_qty = details.get("questions_to_attempt")
            marks_pq = details.get("marks_per_question")

            # 23. All values must be positive integers
            sec_qty_valid = True
            for f, val in [("questions_to_generate", gen_qty), 
                           ("questions_to_attempt", att_qty), 
                           ("marks_per_question", marks_pq)]:
                if not is_positive_integer(val):
                    errors.append(f"Value '{f}' for section '{section_name}' must be a positive integer.")
                    sec_qty_valid = False

            if not sec_qty_valid:
                all_sections_valid = False
                continue

            # 24. questions_to_generate >= questions_to_attempt
            if gen_qty < att_qty:
                errors.append(f"In section '{section_name}': questions_to_generate ({gen_qty}) "
                              f"cannot be less than questions_to_attempt ({att_qty}).")
                all_sections_valid = False

            # 25 & 26. Calculate generated and attempted marks dynamically
            gen_marks = gen_qty * marks_pq
            att_marks = att_qty * marks_pq
            
            total_generated_marks += gen_marks
            total_attempted_marks += att_marks

        # 27, 28, 29. Summed marks validation
        if all_sections_valid:
            if total_marks is not None and is_positive_number(total_marks):
                # 28. Total attempted marks must exactly equal total_marks
                if total_attempted_marks != total_marks:
                    errors.append(f"Total attempted marks from all sections is {total_attempted_marks}, "
                                  f"but paper total marks is {total_marks}.")
            
            # 29. Total generated marks must be >= total attempted marks
            if total_generated_marks < total_attempted_marks:
                errors.append(f"Total generated marks ({total_generated_marks}) must be greater than "
                              f"or equal to total attempted marks ({total_attempted_marks}).")

    # ==========================================
    # Final validation decision
    # ==========================================
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }
