from flask import Blueprint, jsonify

import database as db
from utils.auth import require_admin


stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/api/stats', methods=['GET'])
@require_admin
def get_database_stats():
    """Get database statistics (total papers, questions, etc.)"""
    try:
        stats = db.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"Error in get_database_stats: {str(e)}")
        return jsonify({'error': str(e)}), 500