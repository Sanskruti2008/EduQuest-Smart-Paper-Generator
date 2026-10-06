from flask import Blueprint, jsonify, request

from faculty_store import get_faculty, save_faculty
from utils.auth import require_admin


faculty_bp = Blueprint('faculty', __name__)


@faculty_bp.route('/api/admin/faculty', methods=['GET'])
@require_admin
def get_faculty_endpoint():
    try:
        return jsonify({"success": True, "faculty": get_faculty()}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@faculty_bp.route('/api/admin/faculty', methods=['POST'])
@require_admin
def add_faculty_endpoint():
    try:
        data = request.json or {}
        faculty = get_faculty()
        new_faculty = {
            "id": len(faculty) + 1,
            "name": data.get("name"),
            "course": data.get("course"),
            "role": data.get("role", "Teacher"),
            "status": data.get("status", "Active")
        }
        faculty.append(new_faculty)
        save_faculty(faculty)
        return jsonify({"success": True, "faculty": faculty}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500