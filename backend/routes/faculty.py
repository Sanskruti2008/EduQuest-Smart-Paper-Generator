import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

import database as db
from utils.auth import require_supabase_admin


faculty_bp = Blueprint("faculty", __name__)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_FACULTY_FIELDS = (
    "user_id, auth_user_id, name, role, email, employee_id, department, is_active"
)


def _error(message: str, status: int, *, errors: dict | None = None):
    response = {"success": False, "message": message}
    if errors:
        response["errors"] = errors
    return jsonify(response), status


def _profile_conflicts(
    client, email: str, employee_id: str, exclude_user_id: int | None = None
) -> set[str]:
    result = client.table("User").select("user_id, email, employee_id").execute()
    conflicts: set[str] = set()
    for user in result.data or []:
        if user.get("user_id") == exclude_user_id:
            continue
        if email and str(user.get("email") or "").strip().casefold() == email.casefold():
            conflicts.add("email")
        if (
            employee_id
            and str(user.get("employee_id") or "").strip().casefold()
            == employee_id.casefold()
        ):
            conflicts.add("employee_id")
    return conflicts


def _serialize_faculty(user: dict, assigned_subject_ids: list[int]) -> dict:
    return {
        "user_id": user["user_id"],
        "auth_user_id": user.get("auth_user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "employee_id": user.get("employee_id"),
        "department": user.get("department"),
        "role": "faculty",
        "is_active": bool(user.get("is_active", True)),
        "assigned_subjects_count": len(assigned_subject_ids),
        "assigned_subject_ids": assigned_subject_ids,
    }


def _unique_conflict_field(error: APIError) -> str:
    details = " ".join(
        str(value or "")
        for value in (
            getattr(error, "details", None),
            getattr(error, "message", None),
            error,
        )
    ).lower()
    return "employee_id" if "employee" in details else "email"


@faculty_bp.route("/api/admin/faculty", methods=["GET"])
@require_supabase_admin
def get_faculty_endpoint():
    try:
        client = db.get_supabase_admin_client()
        users = (
            client.table("User")
            .select(_FACULTY_FIELDS)
            .eq("role", "faculty")
            .order("name")
            .execute()
        ).data or []
        user_ids = [user["user_id"] for user in users]

        assignments = []
        if user_ids:
            assignments = (
                client.table("faculty_subject_assignment")
                .select("faculty_id, subject_id")
                .eq("is_active", True)
                .in_("faculty_id", user_ids)
                .execute()
            ).data or []
        assignments_by_faculty: dict[int, list[int]] = {
            user_id: [] for user_id in user_ids
        }
        for assignment in assignments:
            assignments_by_faculty[assignment["faculty_id"]].append(
                assignment["subject_id"]
            )

        faculty = [
            _serialize_faculty(user, assignments_by_faculty[user["user_id"]])
            for user in users
        ]
        return jsonify({"success": True, "faculty": faculty}), 200
    except Exception:
        current_app.logger.exception("Unable to load faculty records")
        return _error("Unable to load faculty records.", 500)


@faculty_bp.route("/api/admin/faculty", methods=["POST"])
@require_supabase_admin
def add_faculty_endpoint():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Invalid faculty data.", 400)

    name = data.get("name")
    employee_id = data.get("employee_id")
    email = data.get("email")
    department = data.get("department")
    password = data.get("password")
    errors: dict[str, str] = {}
    if not isinstance(name, str) or not name.strip():
        errors["name"] = "Full name is required."
    if not isinstance(employee_id, str) or not employee_id.strip():
        errors["employee_id"] = "Employee ID is required."
    if not isinstance(email, str) or not email.strip():
        errors["email"] = "Email is required."
    elif not _EMAIL_PATTERN.fullmatch(email.strip()):
        errors["email"] = "Enter a valid email address."
    if not isinstance(department, str) or not department.strip():
        errors["department"] = "Department is required."
    if not isinstance(password, str) or len(password) < 8:
        errors["password"] = "Password must be at least 8 characters."
    if "is_active" in data and not isinstance(data["is_active"], bool):
        errors["is_active"] = "Account status must be active or inactive."
    if errors:
        return _error("Invalid faculty data.", 400, errors=errors)

    normalized_email = email.strip().lower()
    normalized_employee_id = employee_id.strip()
    try:
        client = db.get_supabase_admin_client()
        conflicts = _profile_conflicts(
            client, normalized_email, normalized_employee_id
        )
        if conflicts:
            return _error(
                "A faculty account with this email or employee ID already exists.",
                409,
                errors={
                    field: "This value is already in use."
                    for field in conflicts
                },
            )

        try:
            auth_response = client.auth.admin.create_user(
                {
                    "email": normalized_email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"name": name.strip()},
                }
            )
        except AuthApiError as exc:
            if str(exc.code).lower() == "email_exists":
                return _error(
                    "A faculty account with this email or employee ID already exists.",
                    409,
                    errors={"email": "This email is already in use."},
                )
            if str(exc.code).lower() in {"weak_password", "password_too_short"}:
                return _error(
                    "Invalid faculty data.",
                    400,
                    errors={"password": "Choose a stronger password."},
                )
            current_app.logger.warning(
                "Supabase rejected faculty account creation (status=%s, code=%s)",
                exc.status,
                exc.code,
            )
            return _error("Unable to create faculty account.", 500)

        auth_user = auth_response.user
        auth_user_id = getattr(auth_user, "id", None)
        if not auth_user_id:
            current_app.logger.error(
                "Supabase created a faculty account without returning its ID"
            )
            return _error("Unable to create faculty account.", 500)

        profile_data = {
            "auth_user_id": auth_user_id,
            "name": name.strip(),
            "role": "faculty",
            "email": normalized_email,
            "employee_id": normalized_employee_id,
            "department": department.strip(),
            "is_active": data.get("is_active", True),
        }
        try:
            insert_result = client.table("User").insert(profile_data).execute()
            if not insert_result.data:
                raise RuntimeError("Faculty profile insert returned no record.")
        except Exception as exc:
            try:
                client.auth.admin.delete_user(auth_user_id)
            except Exception:
                current_app.logger.exception(
                    "Unable to roll back Supabase Auth user after profile insert failure"
                )
            if isinstance(exc, APIError) and getattr(exc, "code", None) == "23505":
                field = _unique_conflict_field(exc)
                return _error(
                    "A faculty account with this email or employee ID already exists.",
                    409,
                    errors={field: "This value is already in use."},
                )
            current_app.logger.exception("Unable to save the faculty profile")
            return _error("Unable to create faculty account.", 500)

        faculty = _serialize_faculty(insert_result.data[0], [])
        return jsonify(
            {
                "success": True,
                "message": "Faculty account created successfully.",
                "faculty": faculty,
            }
        ), 201
    except Exception:
        current_app.logger.exception("Unable to create faculty account")
        return _error("Unable to create faculty account.", 500)


@faculty_bp.route("/api/admin/faculty/<int:user_id>", methods=["PATCH"])
@require_supabase_admin
def update_faculty_endpoint(user_id: int):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Invalid faculty data.", 400)

    allowed_fields = {"name", "employee_id", "department", "is_active"}
    if set(data) - allowed_fields or not data:
        return _error("Invalid faculty data.", 400)

    updates: dict[str, object] = {}
    errors: dict[str, str] = {}
    for field in ("name", "employee_id", "department"):
        if field in data:
            value = data[field]
            if not isinstance(value, str) or not value.strip():
                errors[field] = f"{field.replace('_', ' ').capitalize()} is required."
            else:
                updates[field] = value.strip()
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors["is_active"] = "Account status must be active or inactive."
        else:
            updates["is_active"] = data["is_active"]
    if errors:
        return _error("Invalid faculty data.", 400, errors=errors)

    try:
        client = db.get_supabase_admin_client()
        existing = (
            client.table("User")
            .select(_FACULTY_FIELDS)
            .eq("user_id", user_id)
            .eq("role", "faculty")
            .limit(1)
            .execute()
        ).data
        if not existing:
            return _error("Faculty account not found.", 404)

        if "employee_id" in updates:
            conflicts = _profile_conflicts(
                client,
                str(existing[0].get("email") or ""),
                str(updates["employee_id"]),
                exclude_user_id=user_id,
            )
            if "employee_id" in conflicts:
                return _error(
                    "An account with this employee ID already exists.",
                    409,
                    errors={"employee_id": "This employee ID is already in use."},
                )

        result = (
            client.table("User")
            .update(updates)
            .eq("user_id", user_id)
            .eq("role", "faculty")
            .execute()
        )
        if not result.data:
            return _error("Faculty account not found.", 404)
        active_assignments = (
            client.table("faculty_subject_assignment")
            .select("subject_id")
            .eq("faculty_id", user_id)
            .eq("is_active", True)
            .execute()
        ).data or []
        faculty = _serialize_faculty(
            result.data[0], [item["subject_id"] for item in active_assignments]
        )
        return jsonify(
            {
                "success": True,
                "message": "Faculty account updated successfully.",
                "faculty": faculty,
            }
        ), 200
    except APIError as exc:
        if getattr(exc, "code", None) == "23505":
            return _error(
                "An account with this employee ID already exists.",
                409,
                errors={"employee_id": "This employee ID is already in use."},
            )
        current_app.logger.exception("Unable to update faculty account")
        return _error("Unable to update faculty account.", 500)
    except Exception:
        current_app.logger.exception("Unable to update faculty account")
        return _error("Unable to update faculty account.", 500)


@faculty_bp.route("/api/admin/subjects", methods=["GET"])
@require_supabase_admin
def get_subjects_endpoint():
    try:
        result = (
            db.get_supabase_admin_client()
            .table("subject")
            .select("subject_id, subject_name, subject_code, branch, semester")
            .order("subject_name")
            .execute()
        )
        return jsonify({"success": True, "subjects": result.data or []}), 200
    except Exception:
        current_app.logger.exception("Unable to load subjects for faculty assignment")
        return _error("Unable to load subjects.", 500)


@faculty_bp.route(
    "/api/admin/faculty/<int:user_id>/subjects", methods=["POST"]
)
@require_supabase_admin
def assign_subject_endpoint(user_id: int):
    data = request.get_json(silent=True)
    subject_id = data.get("subject_id") if isinstance(data, dict) else None
    if isinstance(subject_id, bool):
        subject_id = None
    try:
        subject_id = int(subject_id)
    except (TypeError, ValueError):
        subject_id = None
    if subject_id is None or subject_id <= 0:
        return _error(
            "Invalid subject.",
            400,
            errors={"subject_id": "Select a valid subject."},
        )

    try:
        client = db.get_supabase_admin_client()
        faculty = (
            client.table("User")
            .select("user_id")
            .eq("user_id", user_id)
            .eq("role", "faculty")
            .eq("is_active", True)
            .limit(1)
            .execute()
        ).data
        if not faculty:
            return _error("Active faculty account not found.", 404)

        subject = (
            client.table("subject")
            .select("subject_id")
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        ).data
        if not subject:
            return _error("Subject not found.", 404)

        assignment_table = client.table("faculty_subject_assignment")
        existing = (
            assignment_table.select("faculty_id, subject_id, is_active")
            .eq("faculty_id", user_id)
            .eq("subject_id", subject_id)
            .limit(1)
            .execute()
        ).data
        assignment_data = {
            "faculty_id": user_id,
            "subject_id": subject_id,
            "assigned_by": g.current_user["user_id"],
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
        }
        if existing:
            if existing[0].get("is_active"):
                return jsonify(
                    {"success": True, "message": "Subject is already assigned."}
                ), 200
            assignment_data.pop("faculty_id")
            assignment_data.pop("subject_id")
            result = (
                assignment_table.update(assignment_data)
                .eq("faculty_id", user_id)
                .eq("subject_id", subject_id)
                .execute()
            )
        else:
            result = assignment_table.insert(assignment_data).execute()
        if not result.data:
            raise RuntimeError("Subject assignment returned no record.")
        return jsonify(
            {"success": True, "message": "Subject assigned successfully."}
        ), 200
    except APIError as exc:
        if getattr(exc, "code", None) == "23505":
            return _error("Subject is already assigned.", 409)
        current_app.logger.exception("Unable to assign subject to faculty")
        return _error("Unable to assign subject.", 500)
    except Exception:
        current_app.logger.exception("Unable to assign subject to faculty")
        return _error("Unable to assign subject.", 500)
