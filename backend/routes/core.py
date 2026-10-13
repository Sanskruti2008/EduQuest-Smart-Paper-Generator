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

def generate_chat_response(message: str) -> str:
    if any(word in message for word in ['hello', 'hi', 'hey', 'greetings', 'hola', 'namaste']):
        return "Hello! I'm your EduQuest Smart Paper generation System assistant. I can help you with question papers, settings, export options, and more."
    if any(word in message for word in ['question', 'paper', 'exam', 'test', 'assessment']):
        return "I can help you manage the question bank, review uploaded papers, and inspect syllabus and similarity information."
    if message in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
        return "Great! What specific aspect would you like to know more about?"
    if message in ['no', 'nope', 'nah']:
        return "No problem! Is there anything else I can help you with?"
    return "I'm here to help you with EduQuest Smart Paper generation System. Ask me about the question bank, uploaded papers, syllabus analysis, or similarity detection."

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
