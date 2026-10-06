from flask import Blueprint, request, jsonify, current_app
import os, re, json, time
from difflib import SequenceMatcher
import bcrypt
from groq import Groq
from dotenv import load_dotenv
import database as db
from utils.auth import _generate_admin_token, _generate_role_token, require_admin

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
        return "Hello! I'm your EduQuest.ai assistant. I can help you with question papers, settings, export options, and more."
    if any(word in message for word in ['question', 'paper', 'exam', 'test', 'assessment']):
        return "I can help you manage the question bank, review uploaded papers, and inspect syllabus and similarity information."
    if message in ['yes', 'yeah', 'yep', 'sure', 'ok', 'okay']:
        return "Great! What specific aspect would you like to know more about?"
    if message in ['no', 'nope', 'nah']:
        return "No problem! Is there anything else I can help you with?"
    return "I'm here to help you with EduQuest.ai. Ask me about the question bank, uploaded papers, syllabus analysis, or similarity detection."

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


@core_bp.route('/api/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.json or {}
        username = data.get('username') or data.get('email')
        password = data.get('password')
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        # Debug: log that a login attempt occurred (do NOT log raw passwords in production)
        try:
            print(f"[AUTH] Login attempt: username={username}, password_len={len(password) if password else 0}")
        except Exception:
            pass
        # Dev fallback: allow a local admin when Supabase isn't configured or
        # when FLASK_DEBUG is truthy. Controlled via env variables so it is
        # explicit and safe for local development only.
        supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_KEY', '')
        debug_mode = current_app.debug or os.getenv('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
        dev_username = os.getenv('DEV_ADMIN_USERNAME', 'admin@eduquest.ai')
        dev_password = os.getenv('DEV_ADMIN_PASSWORD', 'adminpass')
        if debug_mode and username == dev_username and password == dev_password:
            print(f"[AUTH] Dev fallback login success for {username}")
            return jsonify({'success': True, 'token': _generate_admin_token(username), 'admin': {'username': username}})

        # Attempt to fetch admin user from Supabase. If the lookup fails due to
        # missing configuration or network issues, allow a local debug fallback
        # only when Supabase keys are not set/placeholder or when running in
        # debug mode. This makes local development easier while keeping
        # production behaviour unchanged.
        try:
            admin_user = db.get_admin_user(username)
        except Exception as e:
            print(f"[AUTH] Supabase lookup failed: {e}")
            admin_user = None

        if admin_user:
            password_hash = (admin_user.get('password_hash') or '').encode('utf-8')
            if not password_hash or not bcrypt.checkpw(password.encode('utf-8'), password_hash):
                print(f"[AUTH] Invalid credentials for user {username}: bcrypt mismatch")
                return jsonify({'error': 'Invalid credentials'}), 401
            return jsonify({'success': True, 'token': _generate_admin_token(username), 'admin': {'username': admin_user.get('username')}})

        if not supabase_key or supabase_key.startswith('REPLACE') or debug_mode:
            dev_username = os.getenv('DEV_ADMIN_USERNAME', 'admin@eduquest.ai')
            dev_password = os.getenv('DEV_ADMIN_PASSWORD', 'adminpass')
            if username == dev_username and password == dev_password:
                print(f"[AUTH] Dev fallback login success for {username}")
                return jsonify({'success': True, 'token': _generate_admin_token(username), 'admin': {'username': username}})
        print(f"[AUTH] Invalid credentials for {username}: no matching admin_user and dev fallback not used")
        return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@core_bp.route('/api/faculty/login', methods=['POST'])
def faculty_login():
    data = request.json or {}
    username = data.get('username') or data.get('email')
    password = data.get('password')
    configured_username = os.getenv('DEV_FACULTY_USERNAME', 'faculty@eduquest.ai')
    configured_password = os.getenv('DEV_FACULTY_PASSWORD', 'facultypass')
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    if username != configured_username or password != configured_password:
        return jsonify({'error': 'Invalid faculty credentials'}), 401
    return jsonify({
        'success': True,
        'token': _generate_role_token(username, 'faculty'),
        'faculty': {'username': username},
    })


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
