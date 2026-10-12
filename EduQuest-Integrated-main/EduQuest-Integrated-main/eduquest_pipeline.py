"""End-to-end EduQuest question paper generation pipeline."""

import json
from pathlib import Path

from QP_blueprint.faculty_input_validator import validate_faculty_input
from QP_blueprint.blueprint_processor import create_blueprint
from QP_blueprint.blueprint_validator import validate_blueprint

from paper_generation import generate_question_paper

from Question_Paper_Validator.paper_validator import validate_paper
from Question_Paper_Formatter.paper_formatter import validate_and_format_paper
from Question_Paper_Formatter.docx_generator import generate_docx


def generate_final_question_paper(
    faculty_input,
    output_dir="final_output",
    persist=False,
):
    """
    Complete EduQuest pipeline:

    Faculty Input
        -> Faculty Input Validator
        -> Blueprint Generator
        -> Blueprint Validator
        -> Paper Generation Engine
        -> Paper Validator
        -> Paper Formatter
        -> DOCX Generator
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n========================================")
    print(" EDUQUEST END-TO-END PAPER GENERATION")
    print("========================================")

    # --------------------------------------------------
    # 1. FACULTY INPUT VALIDATION
    # --------------------------------------------------

    faculty_validation = validate_faculty_input(faculty_input)

    if not faculty_validation["valid"]:
        return {
            "status": "FAILED",
            "stage": "FACULTY_INPUT_VALIDATION",
            "errors": faculty_validation["errors"],
        }

    print("[1/7] Faculty Input       = VALID")

    # --------------------------------------------------
    # 2. BLUEPRINT GENERATION
    # --------------------------------------------------

    blueprint = create_blueprint(faculty_input)

    blueprint_path = output_dir / "generated_blueprint.json"

    blueprint_path.write_text(
        json.dumps(blueprint, indent=2),
        encoding="utf-8",
    )

    print("[2/7] Blueprint Generated = PASS")

    # --------------------------------------------------
    # 3. BLUEPRINT VALIDATION
    # --------------------------------------------------

    blueprint_validation = validate_blueprint(blueprint)

    if not blueprint_validation["valid"]:
        return {
            "status": "FAILED",
            "stage": "BLUEPRINT_VALIDATION",
            "errors": blueprint_validation["errors"],
            "blueprint_path": str(blueprint_path),
        }

    print("[3/7] Blueprint           = VALID")

    # --------------------------------------------------
    # 4. PAPER GENERATION ENGINE
    # --------------------------------------------------

    subject = faculty_input["subject"]

    selected_json_path = (
        output_dir / "selected_questions.json"
    )

    persistence_client = None
    if persist:
        try:
            from database import get_supabase_admin_client

            persistence_client = get_supabase_admin_client()
        except Exception:
            return {
                "status": "FAILED",
                "stage": "PERSISTENCE_CONFIGURATION",
                "error": (
                    "PERSISTENCE_CONFIGURATION_ERROR: Server-side Supabase "
                    "service-role client is unavailable."
                ),
            }

    try:
        generation_result = generate_question_paper(
            blueprint=blueprint,
            subject=subject,
            persist=persist,
            output_path=str(selected_json_path),
            persistence_client=persistence_client,
        )

    except Exception as error:
        return {
            "status": "FAILED",
            "stage": "PAPER_GENERATION",
            "error": str(error),
        }

    selected_questions = generation_result["formatter_output"]

    print("[4/7] Paper Generation    = PASS")

    # --------------------------------------------------
    # 5. FINAL PAPER VALIDATION
    # --------------------------------------------------

    try:
        paper_validation = validate_paper(
            blueprint,
            selected_questions,
        )

    except Exception as error:
        return {
            "status": "FAILED",
            "stage": "PAPER_VALIDATION",
            "error": str(error),
        }

    if not paper_validation["valid"]:
        return {
            "status": "FAILED",
            "stage": "PAPER_VALIDATION",
            "errors": paper_validation["errors"],
        }

    print("[5/7] Paper Validation    = VALID")

    # --------------------------------------------------
    # 6. FORMAT PAPER
    # --------------------------------------------------

    is_valid, formatter_errors, formatted_paper = (
        validate_and_format_paper(
            selected_questions,
            blueprint=blueprint,
        )
    )

    if not is_valid:
        return {
            "status": "FAILED",
            "stage": "PAPER_FORMATTING",
            "errors": formatter_errors,
        }

    print("[6/7] Paper Formatter     = PASS")

    # --------------------------------------------------
    # 7. GENERATE DOCX
    # --------------------------------------------------

    final_docx_path = (
        output_dir / "EduQuest_Final_Question_Paper.docx"
    )

    try:
        generate_docx(
            formatted_paper,
            str(final_docx_path),
        )

    except Exception as error:
        return {
            "status": "FAILED",
            "stage": "DOCX_GENERATION",
            "error": str(error),
        }

    print("[7/7] DOCX Generation     = PASS")

    print("\n========================================")
    print(" END-TO-END PIPELINE = PASS")
    print("========================================")
    print(f"Blueprint : {blueprint_path}")
    print(f"Questions : {selected_json_path}")
    print(f"DOCX      : {final_docx_path}")

    return {
        "status": "SUCCESS",
        "blueprint": blueprint,
        "blueprint_path": str(blueprint_path),
        "selected_questions": selected_questions,
        "selected_questions_path": str(selected_json_path),
        "paper_validation": paper_validation,
        "docx_path": str(final_docx_path),
        "generation_result": generation_result,
    }


def run_from_json(
    faculty_input_path,
    output_dir="final_output",
    persist=False,
):
    """Run complete pipeline using faculty-input JSON."""

    faculty_input_path = Path(faculty_input_path)

    with faculty_input_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        faculty_input = json.load(file)

    result = generate_final_question_paper(
        faculty_input=faculty_input,
        output_dir=output_dir,
        persist=persist,
    )

    if result["status"] != "SUCCESS":
        print("\n========================================")
        print(" END-TO-END PIPELINE = FAILED")
        print("========================================")
        print("Stage :", result.get("stage"))

        if result.get("errors"):
            for error in result["errors"]:
                print(" -", error)

        if result.get("error"):
            print("Error :", result["error"])

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="EduQuest end-to-end paper generation"
    )

    parser.add_argument(
        "faculty_input",
        help="Path to faculty input JSON",
    )

    parser.add_argument(
        "--output-dir",
        default="final_output",
        help="Directory for generated files",
    )

    parser.add_argument(
        "--persist",
        action="store_true",
        help="Persist generated paper to database",
    )

    args = parser.parse_args()

    run_from_json(
        faculty_input_path=args.faculty_input,
        output_dir=args.output_dir,
        persist=args.persist,
    )