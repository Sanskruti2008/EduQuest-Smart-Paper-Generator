import json
from faculty_input_validator import validate_faculty_input
from blueprint_processor import process_blueprint
from blueprint_validator import validate_blueprint


input_file = "sample_data/faculty_input_OPS.json"
output_file = "sample_data/blueprint_OPS.json"


# Load and validate faculty input first
with open(input_file, "r") as file:
    faculty_data = json.load(file)

validation_result = validate_faculty_input(faculty_data)
if not validation_result["valid"]:
    print("\n===== FACULTY INPUT VALIDATION FAILED =====\n")
    for error in validation_result["errors"]:
        print("-", error)
    exit(1)


# Step 1: Process faculty input and create blueprint
blueprint = process_blueprint(
    input_file,
    output_file
)


# Step 2: Validate generated blueprint
validation_result = validate_blueprint(blueprint)


print("\n===== VALIDATION RESULT =====\n")


if validation_result["valid"]:

    print("Blueprint is VALID")

    print("\n===== BLUEPRINT SUMMARY =====\n")

    paper_info = blueprint["paper_information"]
    calculated_values = blueprint["calculated_values"]

    print(
        "Exam Type:",
        paper_info["exam_type"]
    )

    print(
        "Paper Total Marks:",
        paper_info["paper_total_marks"]
    )

    print(
        "Generated Question Marks:",
        calculated_values["generated_question_marks"]
    )

    print(
        "Total Attempted Marks:",
        calculated_values["total_attempted_marks"]
    )

    print(
        "Total Questions to Generate:",
        calculated_values["total_questions_to_generate"]
    )

else:

    print("Blueprint is INVALID")

    print("\nErrors:")

    for error in validation_result["errors"]:
        print("-", error)