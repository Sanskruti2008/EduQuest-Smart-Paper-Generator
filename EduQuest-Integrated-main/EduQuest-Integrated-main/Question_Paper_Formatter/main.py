"""
main.py — Question Paper Formatter entry point

Workflow:
  1. Find the most recent instructions_<request_id>.json in sample_data/.
  2. Load selected_questions.json from sample_data/.
  3. Merge the instructions (from the instructions file) into a minimal
     blueprint dict so the formatter uses faculty-submitted instructions.
  4. Run validate_and_format_paper(selected_questions, blueprint=blueprint).
  5. Save the DOCX to output/question_paper_<request_id>.docx (unique per run).
"""

import glob
import os
import sys
from datetime import datetime

from paper_formatter import load_json_file, validate_and_format_paper
from docx_generator import generate_docx


def _find_latest_instructions(sample_data_dir: str):
    """
    Return (request_id, file_path) for the most recently modified
    instructions_*.json file in sample_data_dir, or (None, None) if none found.
    """
    pattern = os.path.join(sample_data_dir, "instructions_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None, None
    latest = max(candidates, key=os.path.getmtime)
    # derive request_id from filename: instructions_<request_id>.json
    basename = os.path.basename(latest)
    request_id = basename[len("instructions_"):-len(".json")]
    return request_id, latest


def main():
    print("=" * 60)
    print("Question Paper Formatter and DOCX Generator")
    print("=" * 60)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    sample_data_dir = os.path.join(current_dir, "sample_data")
    output_dir = os.path.join(current_dir, "output")

    os.makedirs(output_dir, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Find instructions file (carries request_id + faculty instructions)
    # ------------------------------------------------------------------
    request_id, instructions_path = _find_latest_instructions(sample_data_dir)

    instructions = []
    if instructions_path:
        print(f"Loading instructions from: {instructions_path}")
        ok, inst_data = load_json_file(instructions_path)
        if ok and isinstance(inst_data, dict):
            instructions = inst_data.get("instructions") or []
            print(f"  → {len(instructions)} instruction(s) loaded  (request_id: {request_id})")
        else:
            print(f"  WARNING: Could not load instructions file — {inst_data}")
            request_id = None
    else:
        print("No instructions_*.json found in sample_data/ — paper will have no instructions.")

    # Fallback unique id when no instructions file exists
    if not request_id:
        request_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ------------------------------------------------------------------
    # 2. Load selected questions JSON
    # ------------------------------------------------------------------
    sq_path = os.path.join(sample_data_dir, "selected_questions.json")
    if not os.path.exists(sq_path):
        sq_path = os.path.join(sample_data_dir, "selected_questions_sample.json")

    print(f"Loading selected questions from: {sq_path}")
    ok, sq_data = load_json_file(sq_path)
    if not ok:
        print(f"ERROR: {sq_data}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # 3. Build a minimal blueprint so the formatter reads instructions
    #    and section titles from it.
    #    Section titles come from the selected_questions sections themselves
    #    (inline fallback path) since we don't have the full blueprint here.
    # ------------------------------------------------------------------
    blueprint = {
        "instructions": instructions,
        # Empty question_pattern — formatter falls back to inline titles per section
        "question_pattern": {},
    }

    # ------------------------------------------------------------------
    # 4. Validate and format
    # ------------------------------------------------------------------
    print("Validating and formatting...")
    is_valid, errors, formatted_paper = validate_and_format_paper(sq_data, blueprint=blueprint)

    if not is_valid:
        print("\n" + "!" * 50)
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        print("!" * 50)
        sys.exit(1)

    print("Validation passed.")

    # ------------------------------------------------------------------
    # 5. Print summary
    # ------------------------------------------------------------------
    pi = formatted_paper["paper_information"]
    instr = formatted_paper.get("instructions", [])
    print("\n" + "-" * 40)
    print("PAPER SUMMARY")
    print("-" * 40)
    print(f"Subject      : {pi['subject']} ({pi['subject_code']})")
    print(f"Branch / Sem : {pi['branch']} — Semester {pi['semester']}")
    print(f"Exam         : {pi['exam_type']}")
    print(f"Total Marks  : {pi['paper_total_marks']}")
    print(f"Instructions : {len(instr)}")
    print(f"Sections     : {len(formatted_paper['sections'])}")
    print(f"Total Qs     : {formatted_paper['total_generated_questions']}")
    print(f"Total Marks  : {formatted_paper['total_generated_marks']}")
    print("-" * 40)
    for sec_name, sec_data in formatted_paper["sections"].items():
        title_str = f"  ({sec_data['title']})" if sec_data.get("title") else ""
        print(
            f"  {sec_data.get('section_label', sec_name)}{title_str}: "
            f"{sec_data['num_questions']} Qs, "
            f"Attempted marks: {sec_data.get('attempted_marks')}"
        )
    print("-" * 40 + "\n")

    # ------------------------------------------------------------------
    # 6. Generate DOCX — unique filename per request
    # ------------------------------------------------------------------
    docx_filename = f"question_paper_{request_id}.docx"
    docx_path = os.path.join(output_dir, docx_filename)

    print(f"Generating DOCX → {docx_path}")
    try:
        generate_docx(formatted_paper, docx_path)
        size_kb = os.path.getsize(docx_path) // 1024
        print(f"DOCX saved successfully ({size_kb} KB)")
    except Exception as exc:
        print(f"ERROR generating DOCX: {exc}")
        sys.exit(1)

    print("=" * 60)
    print(f"Done.  Output: {docx_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
