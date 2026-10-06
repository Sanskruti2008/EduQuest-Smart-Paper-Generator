from flask import Blueprint, request, jsonify
from services.db_service import get_all_uploaded_papers, get_paper_by_id
from utils.auth import require_admin

papers_bp = Blueprint('papers_bp', __name__)


@papers_bp.route('/api/papers/<int:paper_id>', methods=['GET'])
@require_admin
def paper_details(paper_id):
    try:
        paper = get_paper_by_id(paper_id)
        if not paper:
            return jsonify({'error': 'Paper not found'}), 404
        return jsonify({'success': True, 'paper': paper}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@papers_bp.route('/api/uploaded-papers', methods=['GET'])
@require_admin
def uploaded_papers():
    try:
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        papers = get_all_uploaded_papers(limit=limit, offset=offset)
        return jsonify({'success': True, 'papers': papers, 'count': len(papers), 'limit': limit, 'offset': offset}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
