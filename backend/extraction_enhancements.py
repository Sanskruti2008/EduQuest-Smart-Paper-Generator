"""
Enhanced extraction improvements for OCR and RUA modules
Adds spell checking, grammar validation, and improved marks extraction
"""
import re
from typing import Optional, Tuple
from difflib import get_close_matches

# ─────────────────────────────────────────────────────────────────────────────
# SPELLING CORRECTION DICTIONARY
# ─────────────────────────────────────────────────────────────────────────────

# Common OCR misspellings in MSBTE exam papers
COMMON_MISSPELLINGS = {
    'markeling': 'marketing',
    'wilh': 'with',
    'depariment': 'department',
    'esplain': 'explain',
    'expain': 'explain',
    'stale': 'state',
    'recruitmentt': 'recruitment',
    'analisis': 'analysis',
    'sucessful': 'successful',
    'teh': 'the',
    'recieve': 'receive',
    'occured': 'occurred',
    'bussiness': 'business',
    'neccessary': 'necessary',
    'seperator': 'separator',
    'algoritm': 'algorithm',
    'programm': 'program',
    'datastructure': 'data structure',
    'fucntion': 'function',
    'defintion': 'definition',
    'adress': 'address',
    'proccess': 'process',
    'refernce': 'reference',
    'sinulation': 'simulation',
    'implementaton': 'implementation',
    'optimizaton': 'optimization',
    'explaination': 'explanation',
    'descripion': 'description',
    'applicaton': 'application',
    'enviroment': 'environment',
    'succesful': 'successful',
    'existance': 'existence',
    'maintanance': 'maintenance',
    'personel': 'personnel',
    'pricipal': 'principal',
    'reccomend': 'recommend',
    'seperately': 'separately',
    'begining': 'beginning',
    'comming': 'coming',
    'writting': 'writing',
    'stoping': 'stopping',
    'refering': 'referring',
}

# Academic/technical terms dictionary
TECHNICAL_TERMS = {
    'algorithm', 'database', 'network', 'protocol', 'interface', 'framework',
    'architecture', 'component', 'module', 'function', 'variable', 'parameter',
    'iteration', 'recursion', 'polymorphism', 'inheritance', 'encapsulation',
    'abstraction', 'structure', 'subnetting', 'supernetting', 'encryption',
    'authentication', 'authorization', 'bandwidth', 'throughput', 'latency',
    'topology', 'routing', 'switching', 'gateway', 'firewall', 'proxy',
    'middleware', 'microservice', 'containerization', 'virtualization',
}

# ─────────────────────────────────────────────────────────────────────────────
# SPELL CHECKER AND CORRECTOR
# ─────────────────────────────────────────────────────────────────────────────

def correct_spelling(text: str, confidence_threshold: float = 0.8) -> str:
    """
    Correct common OCR spelling errors in text.
    
    Args:
        text: Text to correct
        confidence_threshold: Only apply corrections above this confidence
    
    Returns:
        Text with corrected spelling
    """
    if not text:
        return text
    
    words = text.split()
    corrected_words = []
    
    for word in words:
        # Check if word is in common misspellings
        if word.lower() in COMMON_MISSPELLINGS:
            corrected_words.append(COMMON_MISSPELLINGS[word.lower()])
            continue
        
        # Check if word contains obvious OCR patterns
        if _is_likely_misspelled(word):
            corrected = _attempt_correction(word)
            if corrected and corrected != word:
                corrected_words.append(corrected)
                continue
        
        corrected_words.append(word)
    
    return ' '.join(corrected_words)


def _is_likely_misspelled(word: str) -> bool:
    """Check if word likely has spelling errors based on OCR patterns."""
    # Multiple repeated letters (unlikely): 'thhis', 'thaaat'
    if re.search(r'([a-z])\1{2,}', word.lower()):
        return True
    
    # Unusual letter combinations
    if re.search(r'[aeiou]{3,}', word.lower()):  # Too many vowels in a row
        return True
    
    # OCR commonly confuses: 0/O, 1/l/I, 5/S, 8/B
    if re.search(r'[01O5S8B]', word):
        return True
    
    return False


def _attempt_correction(word: str) -> str:
    """Attempt to correct word using fuzzy matching."""
    all_words = list(TECHNICAL_TERMS) + list(COMMON_MISSPELLINGS.values())
    
    matches = get_close_matches(word.lower(), all_words, n=1, cutoff=0.6)
    if matches:
        return matches[0]
    
    return word


# ─────────────────────────────────────────────────────────────────────────────
# GRAMMAR AND SYNTAX VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

class GrammarValidator:
    """Validate and fix common grammar errors in extracted questions."""
    
    # Common grammar issues in OCR text
    GRAMMAR_FIXES = [
        # Missing articles
        (r'\b(explain|define|describe|discuss)\s+concept\b', r'\1 the concept'),
        (r'\b(explain|define|describe)\s+([a-z]+)\b(?!\s+(?:of|and|with|in))', 
         r'\1 the \2'),
        
        # Subject-verb agreement issues
        (r'\bdata\s+(?:is|are)\s+', r'data are '),
        (r'\bseries\s+of\s+\w+\s+is\s+', r'series of \1 are '),
        
        # Missing prepositions
        (r'\b(discuss|explain|describe)\s+the\s+importance\b',
         r'\1 the importance of'),
        
        # Tense consistency
        (r'(\w+ed)\s+and\s+(\w+)ing\b', lambda m: m.group(1) + ' and ' + m.group(2) + 'ing'),
        
        # Common OCR grammar issues
        (r'\bwhat\s+is\s+the\s+(\w+)s\b', r'what are the \1s'),
        (r'\bdefine\s+(\w+)s\b', r'define the \1s'),
    ]
    
    @staticmethod
    def validate_question_grammar(text: str) -> Tuple[str, list]:
        """
        Validate and fix grammar in a question.
        
        Args:
            text: Question text to validate
        
        Returns:
            Tuple of (corrected_text, issues_found)
        """
        if not text or len(text) < 10:
            return text, []
        
        corrected = text
        issues = []
        
        # Check for missing capitalization
        if text[0].islower():
            corrected = corrected[0].upper() + corrected[1:]
            issues.append("Missing capitalization at start")
        
        # Check for proper ending punctuation
        if not text.rstrip().endswith(('.', '?', '!')):
            corrected = corrected.rstrip() + '.'
            issues.append("Missing ending punctuation")
        
        # Apply grammar fixes
        for pattern, replacement in GrammarValidator.GRAMMAR_FIXES:
            if isinstance(replacement, str):
                if re.search(pattern, corrected, re.IGNORECASE):
                    new_text = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
                    if new_text != corrected:
                        issues.append(f"Applied grammar fix: {pattern[:30]}...")
                    corrected = new_text
        
        # Check subject-verb-object completeness
        verb_pattern = r'\b(explain|define|describe|discuss|list|write|compare|differentiate|state)\b'
        if re.search(verb_pattern, corrected, re.IGNORECASE):
            # Make sure there's object
            if not GrammarValidator._has_complete_sentence_structure(corrected):
                issues.append("Incomplete sentence structure")
        
        return corrected, issues
    
    @staticmethod
    def _has_complete_sentence_structure(text: str) -> bool:
        """Check if sentence has basic subject-verb-object structure."""
        # Simple heuristic: at least 4 words and contains verb
        words = text.split()
        if len(words) < 4:
            return False
        
        verb_pattern = r'\b(explain|define|describe|discuss|list|write|compare|differentiate|state|analyze|solve|calculate)\b'
        return bool(re.search(verb_pattern, text, re.IGNORECASE))


# ─────────────────────────────────────────────────────────────────────────────
# ENHANCED MARKS EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def extract_marks_enhanced(text: str) -> int:
    """
    Enhanced marks extraction with multiple strategies and fallbacks.
    
    Args:
        text: Text containing mark information
    
    Returns:
        Extracted marks value (defaults to 4)
    """
    if not text:
        return 4
    
    text = str(text).strip()
    
    # STRATEGY 1: Direct patterns (highest confidence)
    marks = _extract_marks_direct(text)
    if marks:
        return marks
    
    # STRATEGY 2: Context-aware patterns
    marks = _extract_marks_contextual(text)
    if marks:
        return marks
    
    # STRATEGY 3: Section-level inference
    marks = _extract_marks_from_section_header(text)
    if marks:
        return marks
    
    # STRATEGY 4: Spelled-out numbers
    marks = _extract_marks_spelled_out(text)
    if marks:
        return marks
    
    # Default
    return 4


def _extract_marks_direct(text: str) -> Optional[int]:
    """Extract marks using direct notation patterns."""
    patterns = [
        # Explicit mark notation: [4], [4 marks], (4), (4 marks)
        r'[\[\(]\s*(\d{1,2})\s*(?:marks?|m|M)?\s*[\]\)]',
        
        # Keyword notation: "Marks: 4", "marks - 5", "4 marks", "4M"
        r'\bmarks?\s*[:=\-]?\s*(\d{1,2})\b',
        r'\b(\d{1,2})\s*(?:marks?|m|M)\b',
        
        # M-notation: "M:4", "M-5", "M4"
        r'\bM[:=\-]?(\d{1,2})\b',
        
        # Attempt notation: "Attempt any 3 (12)" or "Q1: Attempt any 2 (8)"
        r'Attempt\s+any\s+\d+\s*[\(\[]?\s*(\d{1,2})\s*[\)\]]?',
        
        # Explicit question mark notation: "Q1: 4" or "Question 1 - 4 marks".
        # A bare question number such as Q1 is not a mark value.
        r'[Qq](?:uestion)?\s*\d+\s*[\:\-]\s*(\d{1,2})\s*(?:marks?)?\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                marks = int(match.group(1))
                if 1 <= marks <= 50:
                    return marks
            except (ValueError, IndexError):
                continue
    
    return None


def _extract_marks_contextual(text: str) -> Optional[int]:
    """Extract marks using contextual patterns."""
    # MSBTE typical marks: 2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20
    MSBTE_MARKS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]
    
    # Look for any number between 1 and 20
    numbers = re.findall(r'\b(\d{1,2})\b', text)
    
    for num_str in numbers:
        num = int(num_str)
        if num in MSBTE_MARKS:
            return num
    
    return None


def _extract_marks_from_section_header(text: str) -> Optional[int]:
    """Extract marks from section headers like 'Q1: Attempt any 3 (12 marks)'."""
    # Pattern: "Attempt any X (Y marks)" or similar
    # Only use this strategy if it's clearly a section-level instruction
    if 'Attempt' not in text:
        return None
        
    match = re.search(r'Attempt\s+any\s+(\d+)\s*[\(\[]?\s*(\d+)\s*(?:marks?)?[\)\]]?', text, re.IGNORECASE)
    if match:
        try:
            num_attempts = int(match.group(1))
            total_marks = int(match.group(2))
            
            # Calculate marks per question
            if num_attempts > 0 and total_marks > 0:
                marks_each = total_marks // num_attempts
                if 1 <= marks_each <= 50:
                    return marks_each
        except (ValueError, ZeroDivisionError):
            pass
    
    return None


def _extract_marks_spelled_out(text: str) -> Optional[int]:
    """Extract marks written as spelled-out numbers."""
    words_map = {
        'ONE': 1, 'TWO': 2, 'THREE': 3, 'FOUR': 4, 'FIVE': 5,
        'SIX': 6, 'SEVEN': 7, 'EIGHT': 8, 'NINE': 9, 'TEN': 10,
        'TWELVE': 12, 'FOURTEEN': 14, 'FIFTEEN': 15, 'SIXTEEN': 16, 'TWENTY': 20
    }
    
    text_upper = text.upper()
    for word, value in words_map.items():
        if re.search(rf'\b{word}\b\s*(?:marks?)?', text_upper):
            return value
    
    return None


def validate_marks_extraction(question_text: str, extracted_marks: int) -> Tuple[int, float]:
    """
    Validate extracted marks and return confidence score.
    
    Args:
        question_text: The question text
        extracted_marks: The extracted marks value
    
    Returns:
        Tuple of (validated_marks, confidence_score)
    """
    MSBTE_MARKS = [2, 3, 4, 5, 6, 8, 10, 12, 15, 16, 20]
    
    confidence = 0.5  # Base confidence
    
    # Check if marks are in MSBTE typical range
    if extracted_marks in MSBTE_MARKS:
        confidence += 0.3
    elif 1 <= extracted_marks <= 50:
        confidence += 0.1
    
    # Check if marks pattern appeared explicitly in text
    text_lower = question_text.lower()
    if f'{extracted_marks}' in text_lower:
        if any(pat in text_lower for pat in ['[', '(', 'marks', 'mark', 'M:']):
            confidence += 0.2
    
    # Validate final value
    if extracted_marks not in MSBTE_MARKS:
        # If not in typical set, find closest valid mark
        closest = min(MSBTE_MARKS, key=lambda x: abs(x - extracted_marks))
        return closest, min(confidence, 0.7)
    
    return extracted_marks, min(confidence, 1.0)


# ─────────────────────────────────────────────────────────────────────────────
# INTEGRATED ENHANCEMENT FUNCTION
# ─────────────────────────────────────────────────────────────────────────────

def enhance_extracted_question(question_dict: dict) -> dict:
    """
    Enhance an extracted question with spell checking, grammar validation, and marks verification.
    
    Args:
        question_dict: Dictionary with keys: question_text, marks, course_outcome, etc.
    
    Returns:
        Enhanced question dictionary with additional fields
    """
    enhanced = question_dict.copy()
    
    # 1. Spell checking
    if 'question_text' in enhanced:
        original_text = enhanced['question_text']
        corrected_text = correct_spelling(original_text)
        enhanced['question_text'] = corrected_text
        enhanced['spelling_corrections'] = original_text != corrected_text
    
    # 2. Grammar validation
    if 'question_text' in enhanced:
        corrected, grammar_issues = GrammarValidator.validate_question_grammar(enhanced['question_text'])
        enhanced['question_text'] = corrected
        enhanced['grammar_issues'] = grammar_issues
        enhanced['grammar_checked'] = True
    
    # 3. Enhanced marks extraction
    # 3. Enhanced marks extraction
    question_text = enhanced.get('question_text', '')
    try:
        if 'marks' in enhanced and enhanced['marks']:
            # Validate provided marks
            marks_value = enhanced['marks']
            # Convert string marks to int
            if isinstance(marks_value, str):
                try:
                    marks_value = int(marks_value.strip('[]() '))
                except (ValueError, AttributeError):
                    marks_value = extract_marks_enhanced(question_text)
            
            # Validate marks
            validated_marks, confidence = validate_marks_extraction(
                question_text, 
                marks_value
            )
            enhanced['marks'] = validated_marks
            enhanced['marks_confidence'] = confidence
        else:
            # Extract marks from question text if not provided
            marks = extract_marks_enhanced(question_text)
            enhanced['marks'] = marks
            enhanced['marks_source'] = 'enhanced_extraction'
    except Exception as e:
        print(f"Error in marks extraction: {e}")
        # Ensure marks field exists with default
        if 'marks' not in enhanced:
            enhanced['marks'] = 4
    
    # Add enhancement metadata
    enhanced['enhancements_applied'] = True
    enhanced['enhancement_timestamp'] = __import__('datetime').datetime.now().isoformat()
    
    return enhanced


# ─────────────────────────────────────────────────────────────────────────────
# BATCH ENHANCEMENT
# ─────────────────────────────────────────────────────────────────────────────

def enhance_extracted_questions(questions: list) -> list:
    """
    Enhance a batch of extracted questions.
    
    Args:
        questions: List of question dictionaries
    
    Returns:
        List of enhanced question dictionaries
    """
    enhanced_questions = []
    
    for question in questions:
        try:
            enhanced = enhance_extracted_question(question)
            enhanced_questions.append(enhanced)
        except Exception as e:
            print(f"Error enhancing question: {e}")
            enhanced_questions.append(question)  # Keep original if enhancement fails
    
    return enhanced_questions


if __name__ == '__main__':
    # Test the enhancement functions
    print("Testing spelling correction...")
    test_text = "teh algoritm is used for defnition and implementaton of data structur"
    corrected = correct_spelling(test_text)
    print(f"Original: {test_text}")
    print(f"Corrected: {corrected}\n")
    
    print("Testing grammar validation...")
    test_question = "explain the concept of database without proper grammar"
    corrected_q, issues = GrammarValidator.validate_question_grammar(test_question)
    print(f"Original: {test_question}")
    print(f"Corrected: {corrected_q}")
    print(f"Issues: {issues}\n")
    
    print("Testing enhanced marks extraction...")
    test_cases = [
        "Explain the concept [4]",
        "Q1: Attempt any 3 (12 marks)",
        "Define the term with four marks",
        "What is the principle (M:6)",
    ]
    for test in test_cases:
        marks = extract_marks_enhanced(test)
        print(f"Text: {test} → Marks: {marks}")
