import os
import unittest
from unittest.mock import patch

import database as db
from services import ocr_service, grammar_service


class GrammarCheckPerQuestionTest(unittest.TestCase):
    def test_extract_and_clean_runs_per_question_grammar_check(self):
        sample_data = {
            'total_papers': 1,
            'exam_info': {'subject_name': 'Data Structures using C'},
            'papers': [
                {'paper_number': 1, 'questions': [
                    {'question_number': '1', 'question_text': 'This are wrong grammar'},
                    {'question_number': '2', 'question_text': 'Explain the algorithm'}
                ]}
            ]
        }

        with patch('services.ocr_service.extract_questions_from_pdf', return_value=sample_data), \
             patch('services.ocr_service._clean_payload', return_value=(sample_data, {})), \
             patch('services.ocr_service.clean_and_maybe_correct', return_value=sample_data['papers']) as mock_correct:

            result, _ = ocr_service.extract_and_clean('dummy.pdf', subject_context={}, extracted_json_folder=None)

        self.assertIsNotNone(result)
        self.assertEqual(mock_correct.call_count, 1)
        self.assertEqual(len(mock_correct.call_args[0][0]), 1)
        self.assertEqual(len(mock_correct.call_args[0][0][0]['questions']), 2)

    @patch.dict(os.environ, {'GROK_API_KEY': 'xai-test-key'}, clear=False)
    def test_grok_fallback_for_grammar_correction(self):
        text = 'This are wrong grammar and spellng'

        with patch('database.requests.post') as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {
                'choices': [{'message': {'content': '["This is correct grammar and spelling"]'}}]
            }

            corrected = db._correct_texts_with_llm([text], 'xai-test-key', provider='grok')

        self.assertEqual(corrected, ['This is correct grammar and spelling'])

    def test_long_question_with_ocr_typo_still_gets_remote_correction(self):
        text = 'Explain recruitment select ate the use of ERPlection procedure of HRM department'
        self.assertTrue(len(text) >= 24)
        self.assertTrue(db._needs_remote_correction(text))

        with patch('database._correct_texts_with_groq', return_value=['Explain recruitment selection and the use of ERP in the HRM department.']) as mock_correct:
            with patch('database._pick_grammar_api_key', return_value=('fake-key', 'groq')):
                corrected = mock_correct([text])
                self.assertEqual(corrected, ['Explain recruitment selection and the use of ERP in the HRM department.'])

    def test_clean_and_maybe_correct_tracks_original_and_suggested_text(self):
        papers = [{
            'questions': [
                {'question_text': 'This are wrong grammar'}
            ]
        }]

        with patch('database._pick_grammar_api_key', return_value=('fake-key', 'groq')):
            with patch('database._needs_remote_correction', return_value=True):
                with patch('database._correct_texts_with_groq', return_value=['This is correct grammar.']):
                    result = grammar_service.clean_and_maybe_correct(papers)

        self.assertEqual(result[0]['questions'][0]['question_text'], 'This is correct grammar.')
        self.assertEqual(result[0]['questions'][0]['original_question_text'], 'This are wrong grammar')
        self.assertEqual(result[0]['questions'][0]['grammar_suggestion'], 'This is correct grammar.')

    def test_ocr_merge_patterns_are_cleaned_in_question_body(self):
        from ocr_extractor import clean_text

        samples = [
            'Define production management. Explain Nob per in duction wages actco O',
            'Define marketing management. Stat production systemate its importanceco,',
            'Explain recruitment select ate the use of ERPelection procedure of HRM department',
        ]

        cleaned = [clean_text(s) for s in samples]
        self.assertIn('minimum wages', cleaned[0].lower())
        self.assertIn('system and', cleaned[1].lower())
        self.assertIn('ERP selection', cleaned[2])

    def test_common_iom_ocr_artifacts_are_cleaned(self):
        from ocr_extractor import clean_text

        cleaned = clean_text("State the types of production systemsco.")
        self.assertEqual(cleaned, "State the types of production systems.")
        cleaned = clean_text("State the need of disciptine 'n the industry.")
        self.assertIn('discipline in', cleaned.lower())
        cleaned = clean_text("Explain the various managerial skilis Cco O.")
        self.assertNotIn('Cco O', cleaned)
        self.assertIn('managerial skills', cleaned.lower())
        cleaned = clean_text("Explain the role aorganization.")
        self.assertEqual(cleaned, "Explain the role of organization.")
        cleaned = clean_text("Explain the P's of markebng mix.")
        self.assertIn('marketing mix', cleaned.lower())


if __name__ == '__main__':
    unittest.main()
