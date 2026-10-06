import json
from faculty_input_validator import validate_faculty_input

def get_base_valid_data():
    return {
        "branch": "Computer Technology",
        "semester": 4,
        "subject": "Operating System",
        "subject_code": "232145",
        "exam_type": "Final Examination",
        "total_marks": 70,
        "selected_units": ["Unit-I", "Unit-II"],
        "rua_allocation": {
            "Unit-I": {
                "R": 10,
                "U": 15,
                "A": 15,
                "Total": 40
            },
            "Unit-II": {
                "R": 10,
                "U": 10,
                "A": 10,
                "Total": 30
            }
        },
        "difficulty_allocation": {
            "Easy": 20,
            "Medium": 30,
            "Hard": 20
        },
        "co_requirements": ["CO1", "CO2"],
        "question_pattern": {
            "Q1": {
                "questions_to_generate": 10,
                "questions_to_attempt": 5,
                "marks_per_question": 2
            },
            "Q2": {
                "questions_to_generate": 4,
                "questions_to_attempt": 3,
                "marks_per_question": 4
            },
            "Q3": {
                "questions_to_generate": 4,
                "questions_to_attempt": 3,
                "marks_per_question": 4
            },
            "Q4": {
                "questions_to_generate": 4,
                "questions_to_attempt": 3,
                "marks_per_question": 4
            },
            "Q5": {
                "questions_to_generate": 4,
                "questions_to_attempt": 3,
                "marks_per_question": 4
            },
            "Q6": {
                "questions_to_generate": 4,
                "questions_to_attempt": 3,
                "marks_per_question": 4
            }
        }
    }

def run_tests():
    # ==========================================
    # Test A: A valid exam with 1 selected unit.
    # ==========================================
    print("Running Test A: Valid exam with 1 selected unit...")
    data_a = get_base_valid_data()
    data_a["selected_units"] = ["Unit-I"]
    data_a["rua_allocation"] = {
        "Unit-I": {
            "R": 20,
            "U": 25,
            "A": 25,
            "Total": 70
        }
    }
    result_a = validate_faculty_input(data_a)
    assert result_a["valid"] is True, f"Test A failed: {result_a['errors']}"
    print("Test A Passed!")

    # ==========================================
    # Test B: A valid exam with multiple selected units.
    # ==========================================
    print("\nRunning Test B: Valid exam with multiple selected units...")
    data_b = get_base_valid_data()
    result_b = validate_faculty_input(data_b)
    assert result_b["valid"] is True, f"Test B failed: {result_b['errors']}"
    print("Test B Passed!")

    # ==========================================
    # Test C: Invalid input where RUA totals do not equal total_marks.
    # ==========================================
    print("\nRunning Test C: Invalid input where RUA totals do not equal total_marks...")
    data_c = get_base_valid_data()
    # Change RUA total sum to 40 + 20 = 60 instead of 70
    data_c["rua_allocation"]["Unit-II"]["Total"] = 20
    data_c["rua_allocation"]["Unit-II"]["R"] = 5
    data_c["rua_allocation"]["Unit-II"]["U"] = 5
    data_c["rua_allocation"]["Unit-II"]["A"] = 10
    result_c = validate_faculty_input(data_c)
    assert result_c["valid"] is False, "Test C failed: Expected validation failure."
    print("Test C Passed! Errors found as expected:")
    for err in result_c["errors"]:
        print(f" - {err}")

    # ==========================================
    # Test D: Invalid input where attempted marks do not equal total_marks.
    # ==========================================
    print("\nRunning Test D: Invalid input where attempted marks do not equal total_marks...")
    data_d = get_base_valid_data()
    # Change Q6 questions_to_attempt from 3 to 2, reducing attempted total marks to 66
    data_d["question_pattern"]["Q6"]["questions_to_attempt"] = 2
    result_d = validate_faculty_input(data_d)
    assert result_d["valid"] is False, "Test D failed: Expected validation failure."
    print("Test D Passed! Errors found as expected:")
    for err in result_d["errors"]:
        print(f" - {err}")

    # ==========================================
    # Test E: Invalid input with duplicate units.
    # ==========================================
    print("\nRunning Test E: Invalid input with duplicate units...")
    data_e = get_base_valid_data()
    data_e["selected_units"] = ["Unit-I", "Unit-I"]
    result_e = validate_faculty_input(data_e)
    assert result_e["valid"] is False, "Test E failed: Expected validation failure."
    print("Test E Passed! Errors found as expected:")
    for err in result_e["errors"]:
        print(f" - {err}")

    print("\nAll tests completed successfully!")

if __name__ == "__main__":
    run_tests()
