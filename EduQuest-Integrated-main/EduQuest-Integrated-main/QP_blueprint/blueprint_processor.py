import json
from QP_blueprint.rua_scaler import scale_rua_allocation


def load_faculty_input(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def build_question_pattern(question_pattern):
    processed_pattern = {}

    total_questions_to_generate = 0
    total_generated_marks = 0
    total_attempted_marks = 0

    # Works with any number of sections: Q1, Q2, Q3...
    for question_number, details in question_pattern.items():

        questions_to_generate = details.get("questions_to_generate", details.get("number_of_questions", 0))
        questions_to_attempt = details.get("questions_to_attempt", details.get("number_of_questions", 0))
        marks_per_question = details.get("marks_per_question", 0)

        generated_section_marks = (
            questions_to_generate * marks_per_question
        )

        attempted_section_marks = (
            questions_to_attempt * marks_per_question
        )

        section_entry = {
            "questions_to_generate": questions_to_generate,
            "questions_to_attempt": questions_to_attempt,
            "marks_per_question": marks_per_question,
            "generated_section_marks": generated_section_marks,
            "attempted_section_marks": attempted_section_marks,
        }

        # Preserve the faculty-supplied section title exactly as submitted.
        # title is optional â€” omit the key entirely when absent so the blueprint
        # is clean and consumers can use a simple `blueprint["question_pattern"][sec].get("title", "")`
        title = details.get("title", "")
        if title:
            section_entry["title"] = title

        processed_pattern[question_number] = section_entry

        total_questions_to_generate += questions_to_generate
        total_generated_marks += generated_section_marks
        total_attempted_marks += attempted_section_marks

    return (
        processed_pattern,
        total_questions_to_generate,
        total_generated_marks,
        total_attempted_marks
    )


def create_blueprint(faculty_data):

    (
        processed_pattern,
        total_questions,
        generated_marks,
        attempted_marks
    ) = build_question_pattern(
        faculty_data["question_pattern"]
    )

    rua_alloc = faculty_data.get("rua_allocation", {})
    rua_sum = 0
    if isinstance(rua_alloc, dict):
        for u_details in rua_alloc.values():
            if isinstance(u_details, dict):
                rua_sum += u_details.get("Total", u_details.get("R", 0) + u_details.get("U", 0) + u_details.get("A", 0))

    # Scale RUA and difficulty allocations if raw faculty data (attempted_marks total) is provided
    if rua_sum == attempted_marks:
        scaling_result = scale_rua_allocation(faculty_data)
        scaled_rua = scaling_result["rua_allocation"]
        scaled_diff = scaling_result["difficulty_allocation"]
    else:
        scaled_rua = faculty_data.get("rua_allocation")
        scaled_diff = faculty_data.get("difficulty_allocation")

    blueprint = {
        "paper_information": {
            "branch": faculty_data["branch"],
            "semester": faculty_data["semester"],
            "subject": faculty_data["subject"],
            "subject_code": faculty_data["subject_code"],
            "exam_type": faculty_data["exam_type"],
            "paper_total_marks": faculty_data["total_marks"]
        },

        "requirements": {
            "selected_units": faculty_data["selected_units"],
            "rua_allocation": scaled_rua,
            "difficulty_allocation": scaled_diff,
            "co_requirements": faculty_data["co_requirements"]
        },

        # Faculty-supplied instructions preserved verbatim.
        # Empty list when the faculty did not provide any.
        "instructions": list(faculty_data.get("instructions") or []),

        "question_pattern": processed_pattern,

        "calculated_values": {
            "total_questions_to_generate": total_questions,
            "generated_question_marks": generated_marks,
            "total_attempted_marks": attempted_marks
        }
    }

    return blueprint


def save_blueprint(blueprint, output_file):

    with open(output_file, "w") as file:
        json.dump(blueprint, file, indent=4)

    print(f"Blueprint saved successfully in {output_file}")


def process_blueprint(input_file, output_file):

    faculty_data = load_faculty_input(input_file)

    blueprint = create_blueprint(faculty_data)

    save_blueprint(blueprint, output_file)

    return blueprint
