import unittest
from ocr_extractor import validate_and_clean_question


class QuestionValidationPreserveTest(unittest.TestCase):
    def test_valid_question_without_verb_still_accepted(self):
        question = {
            'question_text': 'Difference between machine learning and deep learning',
            'marks': 4,
            'course_outcome': 'CO1',
            'bloom_level': 'K2',
        }

        cleaned = validate_and_clean_question(question)
        self.assertIsNotNone(cleaned)
        self.assertIn('machine learning', cleaned['question_text'].lower())
        self.assertIn('deep learning', cleaned['question_text'].lower())


if __name__ == '__main__':
    unittest.main()
