from flask import Blueprint, request, jsonify, current_app
import os, re, json
from difflib import SequenceMatcher
from groq import Groq
from dotenv import load_dotenv
import database as db
from supabase_auth.errors import AuthApiError

from utils.auth import get_supabase_profile

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'), override=True)

core_bp = Blueprint('core_bp', __name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

QUESTION_DATABASE = [
    {"id": 1, "text": "What is photosynthesis? Explain the process.", "subject": "Biology", "class": "10"},
    {"id": 2, "text": "Explain the process of photosynthesis in plants.", "subject": "Biology", "class": "10"},
    {"id": 3, "text": "Define photosynthesis and describe its importance.", "subject": "Biology", "class": "10"},
    {"id": 4, "text": "What is Newton's first law of motion?", "subject": "Physics", "class": "9"},
    {"id": 5, "text": "State and explain Newton's first law.", "subject": "Physics", "class": "9"},
]


SYSTEM_HELP_TOPICS = [
    (
        {
            'what is eduquest', 'what does eduquest do', 'how does eduquest work',
            'how does the system work', 'how does this system work', 'about eduquest',
            'what is this app', 'what is this website', 'what is this system',
            'what can i do here', 'what can i do on this app', 'what is this for',
            'tell me about this app', 'tell me about the system',
            'tell me about this system', 'how can this help me',
            'why should i use this',
        },
        {'eduquest', 'system', 'work', 'function', 'platform', 'app', 'website', 'purpose'},
        "EduQuest is a smart question-paper management system for faculty and administrators. "
        "It brings together question-paper OCR, question-bank search, syllabus and RUA analysis, "
        "AI-assisted paper generation, validation, review, and PDF/DOCX export in one workflow."
    ),
    (
        {
            'how do i upload a paper', 'how does ocr work', 'what is ocr',
            'how are questions extracted', 'how does question extraction work',
        },
        {'upload', 'ocr', 'extract', 'scanned', 'pdf', 'paper'},
        "To import an existing paper, open Question Paper OCR at /ocr-upload and upload a PDF. "
        "The backend preprocesses the pages, uses Tesseract OCR to convert scanned content to text, "
        "then parses question numbers, sub-questions, marks, and course outcomes. "
        "Review the extracted questions before saving them to the question bank."
    ),
    (
        {
            'how does paper generation work', 'how do i generate a paper',
            'how are question papers generated', 'how to generate question paper',
            'how can i make a paper', 'how do i make a paper',
            'where can i make a paper', 'how can i create a paper',
        },
        {'generate', 'generation', 'paper', 'questions', 'ai'},
        "To make a paper, open the Faculty Dashboard and select Paper Generation from the sidebar "
        "(or use the Paper Generation page). Choose the branch, semester, subject, exam type, total marks, and units. "
        "Then set the question pattern, difficulty split, R/U/A (Remember, Understand, Apply) allocation, "
        "and course outcomes. EduQuest checks that these totals are consistent, selects suitable questions "
        "from the question bank, and opens the generated paper for review before it is finalized or exported."
    ),
    (
        {
            'what is the question bank', 'how does question bank work',
            'how do i search questions', 'where are questions stored',
            'where will i find the question bank', 'where can i find the question bank',
            'how do i find the question bank', 'where is the question bank',
            'how can i open the question bank',
        },
        {'question', 'bank', 'search', 'filter', 'stored', 'reuse'},
        "You can open the Question Bank from the main navigation at /question-bank, or select Question Bank "
        "in the Faculty Dashboard sidebar. It stores extracted and approved questions with metadata such as subject, unit, "
        "marks, difficulty, course outcome, and R/U/A level. Use search and filters to find reusable questions, "
        "inspect similar questions, and select reliable items for generated papers."
    ),
    (
        {
            'how does similarity detection work', 'what is similarity detection',
            'how are duplicate questions found', 'how do you detect similar questions',
        },
        {'similar', 'similarity', 'duplicate', 'duplicates', 'matching'},
        "When you type a question, EduQuest can compare it with existing question-bank items. "
        "It combines text sequence similarity and keyword overlap; where configured, an AI comparison can "
        "also score semantic similarity. A match above the selected threshold is shown so you can review "
        "the existing question before adding another version."
    ),
    (
        {
            'where can i upload a paper', 'where do i upload a paper',
            'how can i upload a question paper', 'where is the ocr upload',
            'how do i upload a question paper',
        },
        {'upload', 'paper', 'ocr', 'question'},
        "To upload an existing question paper, open Question Paper OCR at /ocr-upload. "
        "Upload the PDF, wait for OCR and question extraction to finish, review the results, "
        "and then save the questions to the Question Bank."
    ),
    (
        {
            'where can i find syllabus analysis', 'where is syllabus analysis',
            'how do i open syllabus analysis', 'how can i analyze the syllabus',
        },
        {'syllabus', 'analysis', 'find', 'open'},
        "Open Syllabus Analysis at /syllabus-analyzer. Select a subject to view chapters, "
        "R/U/A coverage, weightage, missing outcomes, comparisons, and study guidance."
    ),
    (
        {
            'what is rua', 'how does rua work', 'what are rua levels',
            'what does remember understand apply mean',
        },
        {'rua', 'remember', 'understand', 'apply', 'learning'},
        "R/U/A represents Remember, Understand, and Apply learning levels. During paper generation, "
        "you allocate the expected marks or questions across these levels for each selected unit. "
        "The allocation is checked against the generated question pool so the paper matches your learning-outcome plan."
    ),
    (
        {
            'what is syllabus analysis', 'how does syllabus analysis work',
            'what can i do with syllabus', 'how do i analyze syllabus',
        },
        {'syllabus', 'analysis', 'chapter', 'weightage', 'study', 'plan'},
        "Syllabus Analysis lets you inspect subjects and chapters, review RUA analysis, view chapter weightage, "
        "identify missing RUA coverage, compare chapters, and open preparation or study-plan guidance. "
        "Use it before generation to balance coverage across the syllabus."
    ),
    (
        {
            'who can use eduquest', 'what are the user roles', 'admin or faculty',
            'what can faculty do', 'what can admin do',
        },
        {'admin', 'faculty', 'role', 'roles', 'permission', 'moderation'},
        "Faculty can manage assigned subjects, upload and review papers, generate papers, and submit work "
        "through moderation. Administrators manage faculty, assignments, review and finalize papers, and "
        "monitor system statistics. Access to protected actions requires the appropriate signed-in role."
    ),
    (
        {
            'how do i export a paper', 'what export formats are supported',
            'can i download the paper', 'how to download paper',
        },
        {'export', 'download', 'pdf', 'docx', 'word', 'format', 'formats'},
        "After reviewing a generated or extracted paper, use the download/export action. EduQuest supports "
        "PDF and DOCX output so the finalized question paper can be printed or shared."
    ),
    (
        {
            'how does validation work', 'what checks are done',
            'how are papers reviewed', 'what happens before finalizing',
        },
        {'validate', 'validation', 'review', 'finalize', 'check', 'marks', 'structure'},
        "Before a paper is finalized, EduQuest checks required metadata and question structure, including "
        "marks totals, question-pattern counts, difficulty allocation, R/U/A allocation, and selected units. "
        "The review workflow lets faculty or administrators correct issues before approval and export."
    ),
]


def _matches_help_topic(message: str, phrases: set, keywords: set) -> bool:
    normalized = preprocess_text(message)
    if normalized in phrases or any(phrase in normalized for phrase in phrases):
        return True
    words = set(normalized.split())
    return len(words.intersection(keywords)) >= min(2, len(keywords))


def generate_chat_response(message: str) -> str:
    normalized_message = preprocess_text(message)
    if any(word in normalized_message.split() for word in ['hello', 'hi', 'hey', 'greetings', 'hola', 'namaste']):
        return "Hello! I'm your EduQuest Smart Paper generation System assistant. I can help you with question papers, settings, export options, and more."
    if normalized_message in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
        return "Great! What specific aspect would you like to know more about?"
    if normalized_message in ['no', 'nope', 'nah']:
        return "No problem! Is there anything else I can help you with?"
    for phrases, keywords, response in SYSTEM_HELP_TOPICS:
        if _matches_help_topic(message, phrases, keywords):
            return response
    return (
        "I don't know the answer to that question. Please specify your question about EduQuest, "
        "such as paper generation, OCR uploads, the question bank, similarity detection, "
        "syllabus/RUA analysis, roles and moderation, validation, or PDF/DOCX export."
    )

def preprocess_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text: str) -> set:
    stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'and', 'or', 'but', 'what', 'how', 'why', 'when', 'where', 'explain', 'describe', 'define', 'state', 'write'}
    words = preprocess_text(text).split()
    return {word for word in words if word not in stop_words and len(word) > 2}

def calculate_similarity(text1: str, text2: str) -> float:
    seq_similarity = SequenceMatcher(None, preprocess_text(text1), preprocess_text(text2)).ratio()
    keywords1 = extract_keywords(text1)
    keywords2 = extract_keywords(text2)
    if not keywords1 or not keywords2:
        keyword_similarity = 0
    else:
        keyword_similarity = len(keywords1.intersection(keywords2)) / len(keywords1.union(keywords2))
    return (keyword_similarity * 0.6) + (seq_similarity * 0.4)

def calculate_similarity_with_groq(question_text: str, db_question_text: str) -> float:
    if not groq_client:
        return calculate_similarity(question_text, db_question_text)
    try:
        prompt = f"""Compare these two questions and rate their similarity from 0.0 to 1.0.\n\nQuestion 1: \"{question_text}\"\nQuestion 2: \"{db_question_text}\"\n\nRespond with ONLY a number between 0.0 and 1.0."""
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=10)
        response = chat_completion.choices[0].message.content.strip()
        return max(0.0, min(1.0, float(response)))
    except Exception:
        return calculate_similarity(question_text, db_question_text)


@core_bp.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'Backend server is running'})


def _login_with_supabase_role(expected_role: str):
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({'error': 'Email and password are required'}), 400
        email = data.get('username') or data.get('email')
        password = data.get('password')
        if (
            not isinstance(email, str)
            or not email.strip()
            or not isinstance(password, str)
            or not password
        ):
            return jsonify({'error': 'Email and password are required'}), 400

        try:
            auth_response = db.create_supabase_auth_client().auth.sign_in_with_password(
                {'email': email.strip(), 'password': password}
            )
        except AuthApiError as exc:
            if exc.status in (400, 401, 422):
                return jsonify({'error': 'Invalid credentials'}), 401
            current_app.logger.exception('Supabase sign-in failed')
            return jsonify({'error': 'Authentication service unavailable'}), 503
        except Exception:
            current_app.logger.exception('Unable to sign in with Supabase')
            return jsonify({'error': 'Authentication service unavailable'}), 503

        session = auth_response.session
        access_token = getattr(session, 'access_token', None)
        if not access_token:
            current_app.logger.error('Supabase sign-in returned no access token')
            return jsonify({'error': 'Authentication service unavailable'}), 503
        try:
            profile = get_supabase_profile(access_token)
        except Exception:
            current_app.logger.exception('Unable to load signed-in user profile')
            return jsonify({'error': 'Authentication service unavailable'}), 503

        if (
            not profile
            or str(profile.get('role', '')).lower() != expected_role
            or not profile.get('is_active', True)
        ):
            return jsonify({'error': 'Invalid credentials'}), 401

        return jsonify({
            'success': True,
            'token': access_token,
            'user': {
                'user_id': profile['user_id'],
                'name': profile.get('name'),
                'email': profile.get('email'),
                'role': expected_role,
            },
        }), 200
    except Exception:
        current_app.logger.exception('Unexpected login failure')
        return jsonify({'error': 'Authentication service unavailable'}), 503


@core_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    return _login_with_supabase_role('admin')


@core_bp.route('/api/faculty/login', methods=['POST'])
def faculty_login():
    return _login_with_supabase_role('faculty')


@core_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json or {}
        user_message = data.get('message', '')
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        return jsonify({'response': generate_chat_response(user_message.lower())})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@core_bp.route('/api/detect-similar-questions', methods=['POST'])
def detect_similar_questions():
    try:
        data = request.json or {}
        question_text = data.get('questionText', '')
        threshold = data.get('threshold', 0.5)
        if not question_text or len(question_text.strip()) < 10:
            return jsonify({'similarQuestions': []})
        input_keywords = extract_keywords(question_text)
        similar_questions = []
        for db_question in QUESTION_DATABASE:
            similarity_score = calculate_similarity_with_groq(question_text, db_question['text'])
            if similarity_score >= threshold:
                similar_questions.append({'id': db_question['id'], 'text': db_question['text'], 'subject': db_question['subject'], 'class': db_question['class'], 'similarityScore': round(similarity_score * 100, 1), 'matchPercentage': f"{round(similarity_score * 100)}%"})
        similar_questions.sort(key=lambda x: x['similarityScore'], reverse=True)
        return jsonify({'similarQuestions': similar_questions[:5], 'count': len(similar_questions[:5]), 'inputKeywords': list(input_keywords)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@core_bp.route('/api/generate-similar-questions', methods=['POST'])
def generate_similar_questions():
    try:
        data = request.json or {}
        original_question = data.get('originalQuestion')
        if not original_question:
            return jsonify({'error': 'Original question is required'}), 400
        # lightweight fallback response if Groq unavailable
        if not groq_client:
            return jsonify({'success': True, 'suggestions': [original_question], 'count': 1})
        # keep existing behavior by returning a single reworded suggestion if API is present
        prompt = f"Generate 5 alternative questions similar to: {original_question}. Return a JSON array of question strings only."
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile", temperature=0.8, max_tokens=1000)
        response_text = chat_completion.choices[0].message.content.strip()
        json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        suggestions = json.loads(json_match.group(0)) if json_match else [original_question]
        suggestions = [str(s).strip() for s in suggestions if str(s).strip()]
        return jsonify({'success': True, 'suggestions': suggestions[:5], 'count': len(suggestions[:5])})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@core_bp.route('/api/generate-new-question', methods=['POST'])
def generate_new_question():
    try:
        data = request.json or {}
        chapter = data.get('chapter')
        difficulty = data.get('difficulty')
        if not chapter or not difficulty:
            return jsonify({'error': 'Chapter and difficulty are required'}), 400
        if not groq_client:
            return jsonify({'error': 'AI service unavailable'}), 500
        prompt = f"Generate one unique exam question for chapter {chapter} at {difficulty} level. Return only the question text."
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile", temperature=0.9, max_tokens=500)
        new_question = chat_completion.choices[0].message.content.strip()
        new_question = re.sub(r'^(Question\s*:?\s*|Q\s*:?\s*|\d+[\.)]\s*)', '', new_question, flags=re.IGNORECASE).strip()
        return jsonify({'success': True, 'newQuestion': new_question})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
