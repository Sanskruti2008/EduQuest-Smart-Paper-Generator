import unittest
import copy
import os
import tempfile
from docx import Document
from paper_formatter import validate_and_format_paper
from docx_generator import generate_docx, get_subquestion_label

class TestPaperFormatter(unittest.TestCase):

    def setUp(self):
        # Base valid mock data to manipulate during testing
        self.valid_raw_data = {
            "instructions": [
                "All Questions are compulsory.",
                "Illustrate your answers with neat sketches wherever necessary.",
                "Figures to the right indicate full marks. CO means Course Outcome."
            ],
            "paper_information": {
                "branch": "Computer Technology",
                "semester": 4,
                "subject": "Operating System",
                "subject_code": "232145",
                "exam_type": "Final Examination",
                "paper_total_marks": 70
            },
            "sections": {
                "Q1": {
                    "title": "Attempt any FIVE",
                    "questions_to_attempt": 5,
                    "questions": [
                        {
                            "canonical_id": "OS001",
                            "question_text": "Define an operating system.",
                            "unit": "Unit-I",
                            "marks": 2,
                            "rua": "R",
                            "difficulty": "Easy",
                            "course_outcome": "CO1"
                        },
                        {
                            "canonical_id": "OS002",
                            "question_text": "What is a system call?",
                            "unit": "Unit-I",
                            "marks": 2,
                            "rua": "R",
                            "difficulty": "Easy",
                            "course_outcome": "CO2"
                        }
                    ]
                },
                "Q2": {
                    "title": "Attempt any THREE",
                    "questions_to_attempt": 3,
                    "questions": [
                        {
                            "canonical_id": "OS003",
                            "question_text": "Explain CPU scheduling algorithms.",
                            "unit": "Unit-II",
                            "marks": 4,
                            "rua": "U",
                            "difficulty": "Medium",
                            "course_outcome": "CO3"
                        }
                    ]
                }
            }
        }

    # =========================================================================
    # Existing Tests (Preserved and Enhanced)
    # =========================================================================

    def test_valid_input(self):
        """Test with valid data structure, ensuring it passes and returns statistics."""
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertIsNotNone(formatted)
        
        # Verify basic mappings
        self.assertEqual(formatted["paper_information"]["subject"], "Operating System")
        self.assertEqual(formatted["paper_information"]["paper_total_marks"], 70)
        
        # Verify internal metadata is preserved
        q1_questions = formatted["sections"]["Q1"]["questions"]
        self.assertEqual(q1_questions[0]["canonical_id"], "OS001")
        self.assertEqual(q1_questions[0]["unit"], "Unit-I")
        self.assertEqual(q1_questions[0]["rua"], "R")
        self.assertEqual(q1_questions[0]["difficulty"], "Easy")
        self.assertEqual(q1_questions[0]["course_outcome"], "CO1")

    def test_multiple_dynamic_sections(self):
        """Test formatting with dynamically named sections (e.g. Section_A, Section_B)."""
        data = copy.deepcopy(self.valid_raw_data)
        data["sections"] = {
            "Section_A": {
                "questions": [{"question_text": "Q in A", "marks": 5}]
            },
            "Section_B": {
                "questions": [{"question_text": "Q in B", "marks": 10}]
            },
            "Section_C": {
                "questions": [{"question_text": "Q in C", "marks": 15}]
            }
        }
        is_valid, errors, formatted = validate_and_format_paper(data)
        self.assertTrue(is_valid)
        self.assertIn("Section_A", formatted["sections"])
        self.assertIn("Section_B", formatted["sections"])
        self.assertIn("Section_C", formatted["sections"])
        self.assertEqual(formatted["total_generated_questions"], 3)
        self.assertEqual(formatted["total_generated_marks"], 30)

    def test_empty_sections(self):
        """Test that missing or empty sections fail validation."""
        # Case 1: Empty sections dict
        data1 = copy.deepcopy(self.valid_raw_data)
        data1["sections"] = {}
        is_valid, errors, formatted = validate_and_format_paper(data1)
        self.assertFalse(is_valid)
        self.assertTrue(any("must contain at least one question section" in e for e in errors))

        # Case 2: Missing sections key
        data2 = copy.deepcopy(self.valid_raw_data)
        del data2["sections"]
        is_valid, errors, formatted = validate_and_format_paper(data2)
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing required root field: 'sections'" in e for e in errors))

        # Case 3: Empty questions list in section
        data3 = copy.deepcopy(self.valid_raw_data)
        data3["sections"]["Q1"]["questions"] = []
        is_valid, errors, formatted = validate_and_format_paper(data3)
        self.assertFalse(is_valid)
        self.assertTrue(any("has an empty questions list" in e for e in errors))

    def test_missing_question_text(self):
        """Test that missing or invalid question_text fails validation."""
        # Case 1: missing text field
        data1 = copy.deepcopy(self.valid_raw_data)
        del data1["sections"]["Q1"]["questions"][0]["question_text"]
        is_valid, errors, formatted = validate_and_format_paper(data1)
        self.assertFalse(is_valid)
        self.assertTrue(any("is missing 'question_text'" in e for e in errors))

        # Case 2: empty/whitespace text field
        data2 = copy.deepcopy(self.valid_raw_data)
        data2["sections"]["Q1"]["questions"][0]["question_text"] = "   "
        is_valid, errors, formatted = validate_and_format_paper(data2)
        self.assertFalse(is_valid)
        self.assertTrue(any("must have non-empty string for 'question_text'" in e for e in errors))

    def test_invalid_marks(self):
        """Test that invalid, zero, negative, or non-numeric marks fail validation."""
        # Case 1: Negative marks
        data1 = copy.deepcopy(self.valid_raw_data)
        data1["sections"]["Q1"]["questions"][0]["marks"] = -5
        is_valid, errors, formatted = validate_and_format_paper(data1)
        self.assertFalse(is_valid)
        self.assertTrue(any("Marks must be positive" in e for e in errors))

        # Case 2: Zero marks
        data2 = copy.deepcopy(self.valid_raw_data)
        data2["sections"]["Q1"]["questions"][0]["marks"] = 0
        is_valid, errors, formatted = validate_and_format_paper(data2)
        self.assertFalse(is_valid)
        self.assertTrue(any("Marks must be positive" in e for e in errors))

        # Case 3: Non-numeric marks
        data3 = copy.deepcopy(self.valid_raw_data)
        data3["sections"]["Q1"]["questions"][0]["marks"] = "two"
        is_valid, errors, formatted = validate_and_format_paper(data3)
        self.assertFalse(is_valid)
        self.assertTrue(any("Marks must be a number" in e for e in errors))

    def test_correct_section_marks_calculation(self):
        """Test that marks are summed correctly for each section."""
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)
        # Q1 has Q1_1 (2 marks) + Q1_2 (2 marks) = 4 marks
        self.assertEqual(formatted["sections"]["Q1"]["section_total_marks"], 4)
        self.assertEqual(formatted["sections"]["Q1"]["num_questions"], 2)
        # Q2 has Q2_1 (4 marks) = 4 marks
        self.assertEqual(formatted["sections"]["Q2"]["section_total_marks"], 4)
        self.assertEqual(formatted["sections"]["Q2"]["num_questions"], 1)

    def test_correct_total_marks_calculation(self):
        """Test that total marks are summed correctly for the entire paper."""
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)
        # Total generated questions: 2 in Q1 + 1 in Q2 = 3
        self.assertEqual(formatted["total_generated_questions"], 3)
        # Total generated marks: 4 in Q1 + 4 in Q2 = 8
        self.assertEqual(formatted["total_generated_marks"], 8)

    # =========================================================================
    # New Institutional Format Tests (Tests 1 through 8)
    # =========================================================================

    def test_1_instructions_appear_before_questions(self):
        """Test 1: Verify instructions appear before questions in the generated document."""
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(formatted["instructions"]), 3)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            
            # Extract non-empty paragraph texts in order
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            self.assertTrue(len(paragraphs) >= 4)
            
            # Heading should be Instructions:
            self.assertEqual(paragraphs[0], "Instructions:")
            self.assertIn("All Questions are compulsory.", paragraphs[1])
            self.assertIn("Illustrate your answers with neat sketches", paragraphs[2])
            self.assertIn("Figures to the right indicate full marks", paragraphs[3])
            
            # The first section header should appear AFTER all instructions
            q1_index = next(i for i, text in enumerate(paragraphs) if "Q. 1" in text)
            self.assertGreater(q1_index, 3)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_2_section_title_rendered_exactly(self):
        """Test 2: Verify faculty-provided section title is rendered exactly."""
        data = copy.deepcopy(self.valid_raw_data)
        custom_title = "Attempt any FOUR questions from this section"
        data["sections"]["Q1"]["title"] = custom_title
        
        is_valid, errors, formatted = validate_and_format_paper(data)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["sections"]["Q1"]["title"], custom_title)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            paragraphs = [p.text for p in doc.paragraphs]
            matching = [p for p in paragraphs if custom_title in p]
            self.assertEqual(len(matching), 1)
            self.assertIn("Q. 1  Attempt any FOUR questions from this section", matching[0])
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_3_question_labels_generated_correctly(self):
        """Test 3: Verify subquestions automatically receive sequential labels: a), b), c)..."""
        self.assertEqual(get_subquestion_label(0), "a)")
        self.assertEqual(get_subquestion_label(1), "b)")
        self.assertEqual(get_subquestion_label(2), "c)")
        self.assertEqual(get_subquestion_label(3), "d)")
        self.assertEqual(get_subquestion_label(6), "g)")
        self.assertEqual(get_subquestion_label(25), "z)")
        self.assertEqual(get_subquestion_label(26), "aa)")

        # Verify in generated document tables
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            
            # There should be 2 tables (one for Q1, one for Q2)
            self.assertEqual(len(doc.tables), 2)
            
            # Q1 table labels
            t1 = doc.tables[0]
            self.assertEqual(t1.rows[0].cells[1].text.strip(), "a)")
            self.assertEqual(t1.rows[1].cells[1].text.strip(), "b)")
            
            # Q2 table labels reset and start at a)
            t2 = doc.tables[1]
            self.assertEqual(t2.rows[0].cells[1].text.strip(), "a)")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_4_co_from_selected_question_data(self):
        """Test 4: Verify CO comes directly from selected-question data and is rendered."""
        data = copy.deepcopy(self.valid_raw_data)
        data["sections"]["Q1"]["questions"][0]["course_outcome"] = "CO4"
        data["sections"]["Q1"]["questions"][1]["course_outcome"] = "CO5"

        is_valid, errors, formatted = validate_and_format_paper(data)
        self.assertTrue(is_valid)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            t1 = doc.tables[0]
            self.assertEqual(t1.rows[0].cells[0].text.strip(), "CO4")
            self.assertEqual(t1.rows[1].cells[0].text.strip(), "CO5")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_5_marks_from_selected_question_data(self):
        """Test 5: Verify marks come directly from selected-question data."""
        data = copy.deepcopy(self.valid_raw_data)
        data["sections"]["Q1"]["questions"][0]["marks"] = 3
        data["sections"]["Q1"]["questions"][1]["marks"] = 5

        is_valid, errors, formatted = validate_and_format_paper(data)
        self.assertTrue(is_valid)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            t1 = doc.tables[0]
            self.assertEqual(t1.rows[0].cells[3].text.strip(), "(3)")
            self.assertEqual(t1.rows[1].cells[3].text.strip(), "(5)")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_6_section_marks_generated_dynamically(self):
        """Test 6: Verify section total marks are generated dynamically from question pattern."""
        data = copy.deepcopy(self.valid_raw_data)
        # Q1 has 2 questions of 2 marks, attempt 5 -> 5 * 2 = 10
        data["sections"]["Q1"]["questions_to_attempt"] = 5
        data["sections"]["Q1"]["questions"][0]["marks"] = 2
        
        # Q2 has attempt 3 with 4 marks each -> 3 * 4 = 12
        data["sections"]["Q2"]["questions_to_attempt"] = 3
        data["sections"]["Q2"]["questions"][0]["marks"] = 4

        is_valid, errors, formatted = validate_and_format_paper(data)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["sections"]["Q1"]["attempted_marks"], 10)
        self.assertEqual(formatted["sections"]["Q2"]["attempted_marks"], 12)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            paragraphs = [p.text for p in doc.paragraphs]
            q1_head = next(p for p in paragraphs if "Q. 1" in p)
            q2_head = next(p for p in paragraphs if "Q. 2" in p)
            self.assertIn("(10)", q1_head)
            self.assertIn("(12)", q2_head)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_7_no_institutional_header(self):
        """Test 7: Verify the generated document does NOT contain any institutional header."""
        is_valid, errors, formatted = validate_and_format_paper(self.valid_raw_data)
        self.assertTrue(is_valid)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)

            all_text = " ".join([p.text for p in doc.paragraphs] + [c.text for t in doc.tables for r in t.rows for c in r.cells])

            forbidden_keywords = [
                "Government Polytechnic",
                "GOVERNMENT POLYTECHNIC",
                "Autonomous Institute",
                "Winter Examination",
                "Diploma Programme",
                "Roll No.",
                "Roll No",
                "Duration: 3 Hours",
                "Duration:",
                "Date: ____________"
            ]

            for kw in forbidden_keywords:
                self.assertNotIn(kw, all_text, f"Forbidden header text '{kw}' was found in the generated document!")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_8_generic_paper_pattern(self):
        """Test 8: Verify generic paper with completely different subjects, sections, marks, COs, and titles."""
        generic_data = {
            "instructions": [
                "Attempt any question from Part A and Part B.",
                "Non-programmable scientific calculators are permitted."
            ],
            "paper_information": {
                "branch": "Mechanical Engineering",
                "semester": 2,
                "subject": "Engineering Mathematics",
                "subject_code": "231001",
                "exam_type": "Mid Term",
                "paper_total_marks": 50
            },
            "sections": {
                "Part_A": {
                    "section_label": "PART - A",
                    "title": "Answer ALL questions",
                    "attempted_section_marks": 20,
                    "questions": [
                        {
                            "question_text": "Evaluate the integral of sin(x)dx.",
                            "marks": 5,
                            "course_outcome": "CO1"
                        },
                        {
                            "question_text": "Find the eigenvalues of the matrix A.",
                            "marks": 5,
                            "course_outcome": "CO2"
                        },
                        {
                            "question_text": "Solve the first-order differential equation dy/dx = y.",
                            "marks": 10,
                            "course_outcome": "CO3"
                        }
                    ]
                },
                "Part_B": {
                    "section_label": "PART - B",
                    "title": "Answer any TWO questions",
                    "attempted_section_marks": 30,
                    "questions": [
                        {
                            "question_text": "Apply Laplace transform to solve the initial value problem.",
                            "marks": 15,
                            "course_outcome": "CO4"
                        },
                        {
                            "question_text": "Expand f(x) in a Fourier series in [-pi, pi].",
                            "marks": 15,
                            "course_outcome": "CO4"
                        },
                        {
                            "question_text": "Find the directional derivative of scalar function phi at (1,2,3).",
                            "marks": 15,
                            "course_outcome": "CO5"
                        }
                    ]
                }
            }
        }

        is_valid, errors, formatted = validate_and_format_paper(generic_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.assertEqual(formatted["total_generated_questions"], 6)
        self.assertEqual(formatted["total_generated_marks"], 65)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            self.assertTrue(os.path.exists(temp_path))
            self.assertGreater(os.path.getsize(temp_path), 0)
            
            doc = Document(temp_path)
            paras = [p.text for p in doc.paragraphs if p.text.strip()]
            self.assertEqual(paras[0], "Instructions:")
            self.assertIn("PART - A  Answer ALL questions", paras[4])
            self.assertIn("(20)", paras[4])
            
            # Verify table columns
            self.assertEqual(len(doc.tables), 2)
            t_a = doc.tables[0]
            self.assertEqual(t_a.rows[0].cells[0].text.strip(), "CO1")
            self.assertEqual(t_a.rows[0].cells[1].text.strip(), "a)")
            self.assertEqual(t_a.rows[0].cells[3].text.strip(), "(5)")

            t_b = doc.tables[1]
            self.assertEqual(t_b.rows[0].cells[0].text.strip(), "CO4")
            self.assertEqual(t_b.rows[0].cells[1].text.strip(), "a)")
            self.assertEqual(t_b.rows[0].cells[3].text.strip(), "(15)")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

if __name__ == '__main__':
    unittest.main()


# =============================================================================
# Blueprint-sourced Instructions and Section Titles (Tasks 6–10)
# =============================================================================

class TestBlueprintSourcedInstructions(unittest.TestCase):
    """
    Verify that when a blueprint is supplied to validate_and_format_paper,
    instructions come from the blueprint — not from the selected-questions data.
    """

    def _make_blueprint(self, instructions, section_titles=None):
        """Build a minimal blueprint dict with the given instructions and titles."""
        section_titles = section_titles or {}
        return {
            "instructions": instructions,
            "question_pattern": {
                sec: {"title": title}
                for sec, title in section_titles.items()
            },
        }

    def _make_selected_questions(self, inline_instructions=None):
        """Return a minimal selected_questions dict, optionally with inline instructions."""
        data = copy.deepcopy({
            "paper_information": {
                "branch": "Test Branch",
                "semester": 3,
                "subject": "Test Subject",
                "subject_code": "TS101",
                "exam_type": "Unit Test",
                "paper_total_marks": 10,
            },
            "sections": {
                "Q1": {
                    "questions_to_attempt": 2,
                    "questions": [
                        {"question_text": "Q A", "marks": 5, "course_outcome": "CO1"},
                        {"question_text": "Q B", "marks": 5, "course_outcome": "CO1"},
                    ],
                }
            },
        })
        if inline_instructions is not None:
            data["instructions"] = inline_instructions
        return data

    # ------------------------------------------------------------------
    # Instructions sourced from blueprint
    # ------------------------------------------------------------------

    def test_blueprint_instructions_used_when_blueprint_supplied(self):
        """Blueprint instructions take priority over any inline data."""
        bp_instructions = [
            "All questions are compulsory.",
            "Use neat diagrams wherever necessary.",
        ]
        blueprint = self._make_blueprint(bp_instructions)
        sq = self._make_selected_questions(
            inline_instructions=["This should be ignored."]
        )

        is_valid, errors, formatted = validate_and_format_paper(sq, blueprint=blueprint)
        self.assertTrue(is_valid, errors)
        self.assertEqual(formatted["instructions"], bp_instructions)

    def test_blueprint_instructions_preserved_exactly(self):
        """Instruction text must not be modified during formatting."""
        bp_instructions = [
            "Figures to the right indicate full marks.",
            "CO means Course Outcome.",
            "Use of non-programmable calculator is allowed.",
        ]
        blueprint = self._make_blueprint(bp_instructions)
        sq = self._make_selected_questions()

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=blueprint)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["instructions"], bp_instructions)

    def test_empty_blueprint_instructions_produces_empty_list(self):
        """Empty blueprint instructions list must result in no instructions in output."""
        blueprint = self._make_blueprint([])
        sq = self._make_selected_questions(
            inline_instructions=["Should be ignored."]
        )

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=blueprint)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["instructions"], [])

    def test_no_blueprint_falls_back_to_inline_instructions(self):
        """When blueprint=None, inline instructions from selected_questions are used."""
        inline = ["Inline instruction one.", "Inline instruction two."]
        sq = self._make_selected_questions(inline_instructions=inline)

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=None)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["instructions"], inline)

    def test_different_blueprints_produce_different_instructions(self):
        """Changing blueprint instructions changes formatted output without any code change."""
        sq = self._make_selected_questions()

        bp1 = self._make_blueprint(["Attempt all questions."])
        bp2 = self._make_blueprint(["Attempt any four questions."])

        _, _, formatted1 = validate_and_format_paper(sq, blueprint=bp1)
        _, _, formatted2 = validate_and_format_paper(sq, blueprint=bp2)

        self.assertNotEqual(
            formatted1["instructions"],
            formatted2["instructions"],
        )

    def test_blueprint_instructions_appear_in_docx(self):
        """Blueprint instructions must appear in the generated DOCX document."""
        bp_instructions = [
            "All questions carry equal marks.",
            "Draw diagrams wherever required.",
        ]
        blueprint = self._make_blueprint(bp_instructions)
        sq = self._make_selected_questions()

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=blueprint)
        self.assertTrue(is_valid)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            all_text = " ".join(p.text for p in doc.paragraphs)
            for inst in bp_instructions:
                self.assertIn(inst, all_text,
                    f"Instruction '{inst}' not found in DOCX")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_no_hardcoded_instructions_in_formatted_output(self):
        """
        Providing empty blueprint instructions must produce a DOCX with no
        'Instructions:' heading and no instruction text at all.
        This verifies nothing is hardcoded in the formatter.
        """
        blueprint = self._make_blueprint([])
        sq = self._make_selected_questions()

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=blueprint)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["instructions"], [])

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            all_text = " ".join(p.text for p in doc.paragraphs)
            self.assertNotIn("Instructions:", all_text,
                "Instructions heading must not appear when list is empty")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestBlueprintSourcedSectionTitles(unittest.TestCase):
    """
    Verify that when a blueprint is supplied, section titles come from
    blueprint["question_pattern"][section]["title"].
    """

    def _sq_with_two_sections(self):
        return {
            "paper_information": {
                "branch": "Test", "semester": 1,
                "subject": "Test", "subject_code": "T1",
                "exam_type": "Test", "paper_total_marks": 14,
            },
            "sections": {
                "Q1": {
                    "questions_to_attempt": 5,
                    "questions": [
                        {"question_text": f"Q1-{i}", "marks": 2,
                         "course_outcome": "CO1"}
                        for i in range(7)
                    ],
                },
                "Q2": {
                    "questions_to_attempt": 3,
                    "questions": [
                        {"question_text": f"Q2-{i}", "marks": 4,
                         "course_outcome": "CO2"}
                        for i in range(4)
                    ],
                },
            },
        }

    def _bp_with_titles(self, q1_title, q2_title):
        return {
            "instructions": [],
            "question_pattern": {
                "Q1": {"title": q1_title},
                "Q2": {"title": q2_title},
            },
        }

    def test_blueprint_section_title_used(self):
        """Blueprint section title must appear in formatted section data."""
        sq = self._sq_with_two_sections()
        bp = self._bp_with_titles("Attempt any FIVE", "Attempt any THREE")

        is_valid, errors, formatted = validate_and_format_paper(sq, blueprint=bp)
        self.assertTrue(is_valid, errors)
        self.assertEqual(formatted["sections"]["Q1"]["title"], "Attempt any FIVE")
        self.assertEqual(formatted["sections"]["Q2"]["title"], "Attempt any THREE")

    def test_blueprint_section_title_preserved_exactly(self):
        """Title text must not be modified — no normalisation or inference."""
        custom = "Solve any FOUR of the following problems."
        sq = self._sq_with_two_sections()
        bp = self._bp_with_titles(custom, "Attempt any THREE")

        _, _, formatted = validate_and_format_paper(sq, blueprint=bp)
        self.assertEqual(formatted["sections"]["Q1"]["title"], custom)

    def test_different_section_titles_produce_different_docx(self):
        """Changing blueprint section title changes the DOCX without code changes."""
        sq = self._sq_with_two_sections()
        bp1 = self._bp_with_titles("Attempt any FIVE", "Attempt any THREE")
        bp2 = self._bp_with_titles("Solve any FIVE", "Solve any THREE")

        _, _, fmt1 = validate_and_format_paper(sq, blueprint=bp1)
        _, _, fmt2 = validate_and_format_paper(sq, blueprint=bp2)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as t1:
            p1 = t1.name
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as t2:
            p2 = t2.name
        try:
            generate_docx(fmt1, p1)
            generate_docx(fmt2, p2)
            text1 = " ".join(p.text for p in Document(p1).paragraphs)
            text2 = " ".join(p.text for p in Document(p2).paragraphs)
            self.assertIn("Attempt any FIVE", text1)
            self.assertIn("Solve any FIVE", text2)
            self.assertNotEqual(text1, text2)
        finally:
            for path in (p1, p2):
                if os.path.exists(path):
                    os.remove(path)

    def test_section_title_rendered_in_docx(self):
        """Blueprint section title must appear verbatim in the generated document."""
        sq = self._sq_with_two_sections()
        bp = self._bp_with_titles("Attempt any FIVE", "Attempt any THREE")

        _, _, formatted = validate_and_format_paper(sq, blueprint=bp)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            temp_path = tf.name
        try:
            generate_docx(formatted, temp_path)
            doc = Document(temp_path)
            all_text = " ".join(p.text for p in doc.paragraphs)
            self.assertIn("Attempt any FIVE", all_text)
            self.assertIn("Attempt any THREE", all_text)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_no_blueprint_uses_inline_title_fallback(self):
        """When blueprint=None, inline 'title' from selected_questions section is used."""
        sq = self._sq_with_two_sections()
        sq["sections"]["Q1"]["title"] = "Inline fallback title"

        _, _, formatted = validate_and_format_paper(sq, blueprint=None)
        self.assertEqual(formatted["sections"]["Q1"]["title"], "Inline fallback title")


class TestSelectedQuestionsHasNoInstructions(unittest.TestCase):
    """
    Architecture contract: selected_questions.json must not carry instructions.
    Instructions live in the blueprint only.
    """

    def test_formatter_works_with_selected_questions_without_instructions(self):
        """
        selected_questions.json has no 'instructions' key.
        When passed without a blueprint, instructions in formatted output are empty.
        """
        sq = {
            "paper_information": {
                "branch": "CS", "semester": 4, "subject": "OS",
                "subject_code": "232145", "exam_type": "Final", "paper_total_marks": 70,
            },
            "sections": {
                "Q1": {
                    "questions_to_attempt": 5,
                    "questions": [
                        {"question_text": f"Q{i}", "marks": 2, "course_outcome": "CO1"}
                        for i in range(7)
                    ],
                }
            },
        }
        # Deliberately no 'instructions' key at all
        self.assertNotIn("instructions", sq)

        is_valid, _, formatted = validate_and_format_paper(sq, blueprint=None)
        self.assertTrue(is_valid)
        self.assertEqual(formatted["instructions"], [])


if __name__ == '__main__':
    unittest.main()


# =============================================================================
# Dynamic Table Layout Tests (Task: preserve alignment, dynamic table rows)
# =============================================================================

class TestDynamicTableLayout(unittest.TestCase):
    """
    Verify that the 4-column question table is fully dynamic:
    - CO, label, question text, marks all come from data
    - Any number of questions per section
    - Any number of sections
    - Any marks value
    - Any CO value
    - Long questions wrap inside the text cell without moving other columns
    - Labels are generated automatically per section
    - Fixed column layout enforced (tblLayout fixed)
    """

    # ------------------------------------------------------------------
    # Shared builders
    # ------------------------------------------------------------------

    def _make_paper(self, sections: dict, instructions=None) -> dict:
        """Build a minimal selected_questions dict."""
        # None means use a single default instruction.
        # Empty list [] means no instructions (explicit).
        if instructions is None:
            instructions = ["All questions are compulsory."]
        return {
            "paper_information": {
                "branch": "Test Branch", "semester": 3,
                "subject": "Test Subject", "subject_code": "T001",
                "exam_type": "Test Exam", "paper_total_marks": 100,
            },
            "instructions": instructions,
            "sections": sections,
        }

    def _q(self, text, marks, co="CO1"):
        return {"question_text": text, "marks": marks, "course_outcome": co}

    def _docx_tables(self, sections, instructions=None):
        """Generate a DOCX and return its tables."""
        paper = self._make_paper(sections, instructions)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            return doc.tables
        finally:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    # Column count and structure
    # ------------------------------------------------------------------

    def test_every_table_has_exactly_4_columns(self):
        """Every section table must have exactly 4 columns: CO | label | text | marks."""
        sections = {
            f"Q{i}": {"questions": [self._q(f"Question {i}", 2, f"CO{i}")]}
            for i in range(1, 7)
        }
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables), 6)
        for ti, tbl in enumerate(tables):
            for ri, row in enumerate(tbl.rows):
                self.assertEqual(
                    len(row.cells), 4,
                    f"Table {ti} row {ri} must have 4 cells, got {len(row.cells)}"
                )

    def test_column_0_contains_co(self):
        """Cell 0 must contain the CO value from selected question data."""
        sections = {"Q1": {"questions": [
            self._q("Short question.", 2, "CO3"),
            self._q("Another question.", 4, "CO5"),
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        self.assertEqual(t.rows[0].cells[0].text.strip(), "CO3")
        self.assertEqual(t.rows[1].cells[0].text.strip(), "CO5")

    def test_column_1_contains_sequential_label(self):
        """Cell 1 must contain the generated sequential sub-question label."""
        sections = {"Q1": {"questions": [
            self._q(f"Q {i}", 2) for i in range(5)
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        expected = ["a)", "b)", "c)", "d)", "e)"]
        for ri, exp in enumerate(expected):
            self.assertEqual(t.rows[ri].cells[1].text.strip(), exp)

    def test_column_2_contains_question_text(self):
        """Cell 2 must contain the question text from selected question data."""
        text = "Explain the principle of locality of reference in operating systems."
        sections = {"Q1": {"questions": [self._q(text, 4, "CO2")]}}
        tables = self._docx_tables(sections)
        self.assertIn(text, tables[0].rows[0].cells[2].text)

    def test_column_3_contains_marks(self):
        """Cell 3 must contain the marks value formatted as (N)."""
        sections = {"Q1": {"questions": [
            self._q("Q", 2, "CO1"),
            self._q("Q", 4, "CO2"),
            self._q("Q", 5, "CO3"),
            self._q("Q", 10, "CO4"),
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        self.assertEqual(t.rows[0].cells[3].text.strip(), "(2)")
        self.assertEqual(t.rows[1].cells[3].text.strip(), "(4)")
        self.assertEqual(t.rows[2].cells[3].text.strip(), "(5)")
        self.assertEqual(t.rows[3].cells[3].text.strip(), "(10)")

    # ------------------------------------------------------------------
    # Dynamic question count
    # ------------------------------------------------------------------

    def test_3_questions_creates_3_rows(self):
        sections = {"Q1": {"questions": [self._q(f"Q{i}", 2) for i in range(3)]}}
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables[0].rows), 3)

    def test_5_questions_creates_5_rows(self):
        sections = {"Q1": {"questions": [self._q(f"Q{i}", 2) for i in range(5)]}}
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables[0].rows), 5)

    def test_7_questions_creates_7_rows(self):
        sections = {"Q1": {"questions": [self._q(f"Q{i}", 2) for i in range(7)]}}
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables[0].rows), 7)

    def test_10_questions_creates_10_rows(self):
        sections = {"Q1": {"questions": [self._q(f"Q{i}", 2) for i in range(10)]}}
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables[0].rows), 10)

    # ------------------------------------------------------------------
    # Dynamic section count
    # ------------------------------------------------------------------

    def test_3_sections_create_3_tables(self):
        sections = {
            f"Q{i}": {"questions": [self._q(f"Q{i}a", 4)]}
            for i in range(1, 4)
        }
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables), 3)

    def test_6_sections_create_6_tables(self):
        sections = {
            f"Q{i}": {"questions": [self._q(f"Q{i}a", 4)]}
            for i in range(1, 7)
        }
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables), 6)

    def test_10_sections_create_10_tables(self):
        sections = {
            f"Q{i}": {"questions": [self._q(f"Q{i}a", 2)]}
            for i in range(1, 11)
        }
        tables = self._docx_tables(sections)
        self.assertEqual(len(tables), 10)

    def test_label_resets_per_section(self):
        """Sub-question labels must restart at a) for each new section."""
        sections = {
            "Q1": {"questions": [self._q(f"Q1-{i}", 2) for i in range(4)]},
            "Q2": {"questions": [self._q(f"Q2-{i}", 4) for i in range(3)]},
            "Q3": {"questions": [self._q(f"Q3-{i}", 2) for i in range(5)]},
        }
        tables = self._docx_tables(sections)
        for ti, tbl in enumerate(tables):
            self.assertEqual(
                tbl.rows[0].cells[1].text.strip(), "a)",
                f"Table {ti} first row label should be a)"
            )

    # ------------------------------------------------------------------
    # Dynamic marks values
    # ------------------------------------------------------------------

    def test_mixed_marks_per_section(self):
        """Marks column must correctly render any numeric mark value."""
        marks_values = [2, 4, 5, 6, 8, 10, 12, 15]
        sections = {"Q1": {"questions": [
            self._q(f"Q with {m} marks", m) for m in marks_values
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        for ri, m in enumerate(marks_values):
            self.assertEqual(
                t.rows[ri].cells[3].text.strip(), f"({m})",
                f"Row {ri} marks should be ({m})"
            )

    # ------------------------------------------------------------------
    # Dynamic CO values
    # ------------------------------------------------------------------

    def test_all_co_values_rendered(self):
        """CO column must correctly render any CO string from data."""
        cos = ["CO1", "CO2", "CO3", "CO4", "CO5"]
        sections = {"Q1": {"questions": [
            self._q(f"Q for {co}", 4, co) for co in cos
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        for ri, co in enumerate(cos):
            self.assertEqual(
                t.rows[ri].cells[0].text.strip(), co,
                f"Row {ri} CO should be {co}"
            )

    # ------------------------------------------------------------------
    # Long question wrapping
    # ------------------------------------------------------------------

    def test_long_question_text_stored_in_cell_2(self):
        """
        A question that would wrap to multiple lines must be stored
        entirely in cell 2 — not split across columns.
        """
        long_text = (
            "Explain in detail the concept of virtual memory in operating systems, "
            "including the role of page tables, the translation lookaside buffer, "
            "demand paging, page replacement algorithms such as FIFO, LRU and Optimal, "
            "and the effects of thrashing on system performance."
        )
        sections = {"Q1": {"questions": [self._q(long_text, 4, "CO2")]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        row = t.rows[0]

        # CO column must have only CO text
        self.assertEqual(row.cells[0].text.strip(), "CO2")
        # Label column must have only the label
        self.assertEqual(row.cells[1].text.strip(), "a)")
        # Marks column must have only the marks
        self.assertEqual(row.cells[3].text.strip(), "(4)")
        # Full question text must be in cell 2
        self.assertIn("virtual memory", row.cells[2].text)
        self.assertIn("thrashing", row.cells[2].text)

    def test_short_and_long_questions_in_same_section(self):
        """Short and long questions must both fit correctly in the same table."""
        sections = {"Q1": {"questions": [
            self._q("Define OS.", 2, "CO1"),
            self._q(
                "Explain the concept of kernel and its responsibilities "
                "in process scheduling, memory management, and I/O handling.",
                4, "CO2"
            ),
            self._q("What is a system call?", 2, "CO3"),
        ]}}
        tables = self._docx_tables(sections)
        t = tables[0]
        self.assertEqual(len(t.rows), 3)
        self.assertEqual(t.rows[0].cells[0].text.strip(), "CO1")
        self.assertEqual(t.rows[1].cells[0].text.strip(), "CO2")
        self.assertEqual(t.rows[2].cells[0].text.strip(), "CO3")
        self.assertEqual(t.rows[0].cells[3].text.strip(), "(2)")
        self.assertEqual(t.rows[1].cells[3].text.strip(), "(4)")
        self.assertEqual(t.rows[2].cells[3].text.strip(), "(2)")

    # ------------------------------------------------------------------
    # Fixed layout enforcement
    # ------------------------------------------------------------------

    def test_table_column_widths_are_not_equal(self):
        """
        tblGrid must use narrow CO/label/marks columns — not four equal widths.
        Equal columns (~1.5 in each) caused excessive horizontal gaps.
        """
        from docx.oxml.ns import qn as _qn
        sections = {"Q1": {"questions": [self._q("Define OS.", 2, "CO1")]}}
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            tbl = doc.tables[0]
            grid_cols = tbl._tbl.findall(_qn("w:tblGrid"))[0]
            widths = [
                int(col.get(_qn("w:w")))
                for col in grid_cols.findall(_qn("w:gridCol"))
            ]
            self.assertEqual(len(widths), 4)
            # Text column must be wider than every metadata column
            self.assertGreater(widths[2], widths[0])
            self.assertGreater(widths[2], widths[1])
            self.assertGreater(widths[2], widths[3])
            # Metadata columns must stay narrow (< 0.5 in = 720 twips)
            for w in (widths[0], widths[1], widths[3]):
                self.assertLess(w, 720, f"Metadata column too wide: {w} twips")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_table_has_fixed_layout(self):
        """
        The tblLayout element must be set to 'fixed' so Word does not
        auto-resize columns when question text is long.
        """
        from docx.oxml.ns import qn as _qn
        sections = {"Q1": {"questions": [
            self._q("A very long question " * 10, 4, "CO1")
        ]}}
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            tbl = doc.tables[0]
            tblPr = tbl._tbl.tblPr
            tblLayout = tblPr.find(_qn("w:tblLayout"))
            self.assertIsNotNone(tblLayout, "tblLayout element must be present")
            layout_type = tblLayout.get(_qn("w:type"))
            self.assertEqual(layout_type, "fixed",
                             "tblLayout type must be 'fixed' to prevent column reflow")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_table_has_zero_cell_spacing(self):
        """tblCellSpacing must be 0 to prevent Word's default inter-cell gap."""
        from docx.oxml.ns import qn as _qn
        sections = {"Q1": {"questions": [self._q("Q", 2)]}}
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            tbl = doc.tables[0]
            tblPr = tbl._tbl.tblPr
            tblCS = tblPr.find(_qn("w:tblCellSpacing"))
            self.assertIsNotNone(tblCS)
            self.assertEqual(tblCS.get(_qn("w:w")), "0")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_table_has_zero_indent(self):
        """tblInd must be 0 so the table aligns with the left margin."""
        from docx.oxml.ns import qn as _qn
        sections = {"Q1": {"questions": [self._q("Q", 2)]}}
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            tbl = doc.tables[0]
            tblPr = tbl._tbl.tblPr
            tblInd = tblPr.find(_qn("w:tblInd"))
            self.assertIsNotNone(tblInd)
            self.assertEqual(tblInd.get(_qn("w:w")), "0")
        finally:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    # Font applied explicitly to all cells
    # ------------------------------------------------------------------

    def test_font_applied_to_all_table_cells(self):
        """Every cell run must have font explicitly set — no Word defaults."""
        sections = {"Q1": {"questions": [
            self._q("Define OS.", 2, "CO1"),
            self._q("Explain kernel.", 4, "CO2"),
        ]}}
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            tbl = doc.tables[0]
            for ri, row in enumerate(tbl.rows):
                for ci, cell in enumerate(row.cells):
                    for para in cell.paragraphs:
                        for run in para.runs:
                            self.assertIsNotNone(
                                run.font.name,
                                f"Row {ri} cell {ci} run must have explicit font"
                            )
                            self.assertIsNotNone(
                                run.font.size,
                                f"Row {ri} cell {ci} run must have explicit font size"
                            )
        finally:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    # Dynamic instructions
    # ------------------------------------------------------------------

    def test_zero_instructions_no_block(self):
        """When no instructions are provided, no Instructions block is generated."""
        paper = self._make_paper(
            {"Q1": {"questions": [self._q("Q", 2)]}},
            instructions=[]
        )
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            all_text = " ".join(p.text for p in Document(path).paragraphs)
            self.assertNotIn("Instructions:", all_text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_seven_instructions_all_rendered(self):
        """All 7 instructions must appear in order in the generated document."""
        instr = [f"Instruction number {i}." for i in range(1, 8)]
        paper = self._make_paper(
            {"Q1": {"questions": [self._q("Q", 2)]}},
            instructions=instr
        )
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            all_text = " ".join(p.text for p in Document(path).paragraphs)
            for inst in instr:
                self.assertIn(inst, all_text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    # Dynamic section titles
    # ------------------------------------------------------------------

    def test_section_titles_different_per_section(self):
        """Each section's dynamic title must appear in the document."""
        titles = {
            "Q1": "Attempt any FIVE",
            "Q2": "Attempt any THREE",
            "Q3": "Answer ALL questions",
        }
        sections = {
            sec: {"title": title, "questions": [self._q(f"Q in {sec}", 2)]}
            for sec, title in titles.items()
        }
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            all_text = " ".join(p.text for p in Document(path).paragraphs)
            for title in titles.values():
                self.assertIn(title, all_text)
        finally:
            if os.path.exists(path):
                os.remove(path)

    # ------------------------------------------------------------------
    # No institution header
    # ------------------------------------------------------------------

    def test_no_institution_header_in_any_scenario(self):
        """Generated document must never contain institutional header content."""
        sections = {
            f"Q{i}": {"questions": [self._q(f"Question {i}", 4)]}
            for i in range(1, 4)
        }
        tables = self._docx_tables(sections)
        # Build full text including table cells
        paper = self._make_paper(sections)
        _, _, formatted = validate_and_format_paper(paper)
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tf:
            path = tf.name
        try:
            generate_docx(formatted, path)
            doc = Document(path)
            all_text = " ".join(
                [p.text for p in doc.paragraphs] +
                [c.text for t in doc.tables for r in t.rows for c in r.cells]
            )
            forbidden = [
                "Government Polytechnic", "GOVERNMENT POLYTECHNIC",
                "Roll No", "Duration:", "Diploma Programme",
            ]
            for kw in forbidden:
                self.assertNotIn(kw, all_text)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
