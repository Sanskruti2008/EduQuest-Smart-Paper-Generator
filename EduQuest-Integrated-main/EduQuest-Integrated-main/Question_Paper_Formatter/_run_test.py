"""Temporary test runner — runs formatter on selected_questions.json."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from paper_formatter import load_json_file, validate_and_format_paper
from docx_generator import generate_docx

input_path  = os.path.join(os.path.dirname(__file__), "sample_data", "selected_questions.json")
output_path = os.path.join(os.path.dirname(__file__), "output", "selected_questions_paper.docx")

ok, result = load_json_file(input_path)
if not ok:
    print("LOAD FAILED:", result)
    sys.exit(1)

valid, errors, formatted = validate_and_format_paper(result)
if not valid:
    print("VALIDATION FAILED:")
    for e in errors:
        print(" -", e)
    sys.exit(1)

pi = formatted["paper_information"]
print("--- COMPATIBILITY: PASS ---")
print("Subject  :", pi["subject"], "("+pi["subject_code"]+")")
print("Branch   :", pi["branch"], " Sem", pi["semester"])
print("Exam     :", pi["exam_type"])
print("Marks    :", pi["paper_total_marks"])
print("Sections :", len(formatted["sections"]))
print("Total Qs :", formatted["total_generated_questions"])
print("Total Marks:", formatted["total_generated_marks"])
print()
for sec, data in formatted["sections"].items():
    print(f"  {sec}: {data['num_questions']} questions, {data['section_total_marks']} marks")

generate_docx(formatted, output_path)
print()
print("DOCX written ->", output_path)
print("SIZE:", os.path.getsize(output_path), "bytes")
