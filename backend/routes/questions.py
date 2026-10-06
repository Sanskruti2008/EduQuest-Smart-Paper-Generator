from flask import Blueprint, request, jsonify
from services.db_service import search_questions, get_all_questions
from services.similarity_ingestion_service import get_unique_question_bank

questions_bp = Blueprint('questions_bp', __name__)


@questions_bp.route('/api/unique-question-bank', methods=['GET'])
def get_unique_question_bank_endpoint():
    try:
        branch = request.args.get('branch')
        semester = request.args.get('semester')
        subject = request.args.get('subject')
        questions = get_unique_question_bank(
            branch=branch,
            semester=semester,
            subject=subject,
        )
        return jsonify({
            'success': True,
            'questions': questions,
            'count': len(questions),
            'subject': subject,
            'branch': branch,
            'semester': semester,
        }), 200
    except Exception as error:
        return jsonify({
            'success': False,
            'error': str(error),
        }), 500


@questions_bp.route('/api/questions', methods=['GET'])
def get_questions():
    try:
        branch = request.args.get('branch')
        semester = request.args.get('semester')
        subject = request.args.get('subject')
        difficulty = request.args.get('difficulty')
        chapter = request.args.get('chapter')
        bloom_level = request.args.get('bloom_level')
        limit = request.args.get('limit', type=int, default=100)

        questions = get_all_questions(branch, semester, subject, limit)
        if difficulty:
            questions = [q for q in questions if q.get('difficulty') == difficulty]
        if chapter:
            questions = [q for q in questions if q.get('chapter') == chapter]
        if bloom_level:
            questions = [q for q in questions if q.get('bloom_level') == bloom_level]

        return jsonify({'success': True, 'questions': questions, 'count': len(questions)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@questions_bp.route('/api/questions/search', methods=['GET'])
def search_questions_endpoint():
    try:
        search_query = request.args.get('q', '')
        branch = request.args.get('branch')
        semester = request.args.get('semester')
        subject = request.args.get('subject')
        limit = request.args.get('limit', type=int, default=50)

        if not search_query:
            return jsonify({'error': 'Search query (q) is required'}), 400

        questions = search_questions(search_query, branch, semester, subject, limit)
        return jsonify({'success': True, 'questions': questions, 'count': len(questions), 'search_query': search_query}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
