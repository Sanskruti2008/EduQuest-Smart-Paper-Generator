import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, g, jsonify, request
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

import database as db
from utils.auth import (
    require_supabase_admin,
    require_supabase_faculty_profile,
    require_supabase_roles,
)


faculty_bp = Blueprint("faculty", __name__)
_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
_FACULTY_FIELDS = (
    "user_id, auth_user_id, name, role, email, employee_id, department, is_active"
)


@faculty_bp.route("/api/faculty/me", methods=["GET"])
@require_supabase_faculty_profile
def get_current_faculty_endpoint():
    try:
        profile = g.current_user
        assignments = _fetch_faculty_assignments(
            db.get_supabase_admin_client(),
            faculty_id=profile["user_id"],
            active_only=True,
        )
        generation_subject_count = sum(
            1 for assignment in assignments if assignment.get("can_generate", False)
        )
        moderation_subject_count = sum(
            1 for assignment in assignments if assignment.get("can_moderate", False)
        )
        return jsonify({
            "success": True,
            "faculty": {
                field: profile.get(field)
                for field in (
                    "user_id",
                    "auth_user_id",
                    "name",
                    "email",
                    "employee_id",
                    "department",
                    "role",
                    "is_active",
                )
            },
            "responsibilities": {
                "can_generate": generation_subject_count > 0,
                "can_moderate": moderation_subject_count > 0,
                "generation_subject_count": generation_subject_count,
                "moderation_subject_count": moderation_subject_count,
            },
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load the authenticated faculty profile")
        return _error("Unable to load faculty profile.", 500)


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
        "paper_setter_subjects_count": user.get("paper_setter_subjects_count", 0),
        "moderator_subjects_count": user.get("moderator_subjects_count", 0),
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


def _is_missing_table_column_error(error: Exception) -> bool:
    details = " ".join(
        str(value or "")
        for value in (
            getattr(error, "details", None),
            getattr(error, "message", None),
            error,
        )
    ).lower()
    return (
        "does not exist" in details
        or "unknown column" in details
        or (
            "column" in details
            and (
                "not found" in details
                or "could not find" in details
                or "schema cache" in details
            )
        )
    )


def _is_duplicate_key_error(error: Exception) -> bool:
    details = " ".join(
        str(value or "")
        for value in (
            getattr(error, "details", None),
            getattr(error, "message", None),
            error,
        )
    ).lower()
    return (
        getattr(error, "code", None) == "23505"
        or "duplicate key" in details
        or "unique constraint" in details
        or "already exists" in details
    )


def _fetch_faculty_assignments(
    client,
    *,
    faculty_id: int | None = None,
    faculty_ids: list[int] | None = None,
    subject_id: int | None = None,
    active_only: bool | None = None,
    moderation_only: bool = False,
    include_flags: bool = True,
):
    try:
        query = client.table("faculty_subject_assignment").select(
            "faculty_id, subject_id, is_active"
            + (", can_generate, can_moderate" if include_flags else "")
        )
        if faculty_id is not None:
            query = query.eq("faculty_id", faculty_id)
        if faculty_ids is not None:
            query = query.in_("faculty_id", faculty_ids)
        if subject_id is not None:
            query = query.eq("subject_id", subject_id)
        if active_only is not None:
            query = query.eq("is_active", active_only)
        if moderation_only:
            query = query.eq("can_moderate", True)
        rows = (query.execute().data or [])
    except APIError as exc:
        if not _is_missing_table_column_error(exc):
            raise
        fallback_query = client.table("faculty_subject_assignment").select(
            "faculty_id, subject_id, is_active"
        )
        if faculty_id is not None:
            fallback_query = fallback_query.eq("faculty_id", faculty_id)
        if faculty_ids is not None:
            fallback_query = fallback_query.in_("faculty_id", faculty_ids)
        if subject_id is not None:
            fallback_query = fallback_query.eq("subject_id", subject_id)
        if active_only is not None:
            fallback_query = fallback_query.eq("is_active", active_only)
        rows = (fallback_query.execute().data or [])
        for row in rows:
            row.setdefault("can_generate", True)
            row.setdefault("can_moderate", False)
        if moderation_only and not rows:
            return []
        if moderation_only:
            return [row for row in rows if row.get("can_moderate", False)]
        return rows

    for row in rows:
        if not isinstance(row, dict):
            continue
        row.setdefault("can_generate", True)
        row.setdefault("can_moderate", False)
    if moderation_only:
        return [row for row in rows if row.get("can_moderate", False)]
    return rows


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
            assignments = _fetch_faculty_assignments(
                client,
                faculty_ids=user_ids,
                active_only=True,
            )
        assignments_by_faculty: dict[int, list[int]] = {
            user_id: [] for user_id in user_ids
        }
        setter_counts = {user_id: 0 for user_id in user_ids}
        moderator_counts = {user_id: 0 for user_id in user_ids}
        for assignment in assignments:
            assignments_by_faculty[assignment["faculty_id"]].append(
                assignment["subject_id"]
            )
            if assignment.get("can_generate", True):
                setter_counts[assignment["faculty_id"]] += 1
            if assignment.get("can_moderate", False):
                moderator_counts[assignment["faculty_id"]] += 1

        faculty = [
            _serialize_faculty(
                {
                    **user,
                    "paper_setter_subjects_count": setter_counts[user["user_id"]],
                    "moderator_subjects_count": moderator_counts[user["user_id"]],
                },
                assignments_by_faculty[user["user_id"]],
            )
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
            if isinstance(exc, APIError) and _is_duplicate_key_error(exc):
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
        active_assignments = _fetch_faculty_assignments(
            client,
            faculty_id=user_id,
            active_only=True,
        )
        faculty = _serialize_faculty(
            {
                **result.data[0],
                "paper_setter_subjects_count": sum(
                    bool(item.get("can_generate", True))
                    for item in active_assignments
                ),
                "moderator_subjects_count": sum(
                    bool(item.get("can_moderate", False))
                    for item in active_assignments
                ),
            },
            [item["subject_id"] for item in active_assignments],
        )
        return jsonify(
            {
                "success": True,
                "message": "Faculty account updated successfully.",
                "faculty": faculty,
            }
        ), 200
    except APIError as exc:
        if _is_duplicate_key_error(exc):
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
    requested_can_generate = data.get("can_generate") if isinstance(data, dict) else None
    requested_can_moderate = data.get("can_moderate") if isinstance(data, dict) else None
    if (
        isinstance(data, dict)
        and "can_generate" in data
        and not isinstance(requested_can_generate, bool)
    ) or (
        isinstance(data, dict)
        and "can_moderate" in data
        and not isinstance(requested_can_moderate, bool)
    ):
        return _error(
            "Invalid subject responsibilities.",
            400,
            errors={"responsibilities": "Choose valid paper setter or moderator responsibilities."},
        )
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
        existing = _fetch_faculty_assignments(
            client,
            faculty_id=user_id,
            subject_id=subject_id,
            active_only=None,
        )
        if existing:
            existing = existing[:1]
        can_generate = (
            requested_can_generate
            if requested_can_generate is not None
            else existing[0].get("can_generate", True) if existing else True
        )
        can_moderate = (
            requested_can_moderate
            if requested_can_moderate is not None
            else existing[0].get("can_moderate", False) if existing else False
        )
        if not can_generate and not can_moderate:
            return _error(
                "Select at least one responsibility.",
                400,
                errors={"responsibilities": "Choose Paper Setter, Moderator, or both."},
            )
        assignment_data = {
            "faculty_id": user_id,
            "subject_id": subject_id,
            "assigned_by": g.current_user["user_id"],
            "assigned_at": datetime.now(timezone.utc).isoformat(),
            "is_active": True,
            "can_generate": can_generate,
            "can_moderate": can_moderate,
        }
        if existing:
            assignment_data.pop("faculty_id")
            assignment_data.pop("subject_id")
            try:
                result = (
                    assignment_table.update(assignment_data)
                    .eq("faculty_id", user_id)
                    .eq("subject_id", subject_id)
                    .execute()
                )
            except APIError as exc:
                if not _is_missing_table_column_error(exc):
                    raise
                fallback_data = {
                    key: value
                    for key, value in assignment_data.items()
                    if key not in {"can_generate", "can_moderate"}
                }
                result = (
                    assignment_table.update(fallback_data)
                    .eq("faculty_id", user_id)
                    .eq("subject_id", subject_id)
                    .execute()
                )
        else:
            try:
                result = assignment_table.insert(assignment_data).execute()
            except APIError as exc:
                if not _is_missing_table_column_error(exc):
                    raise
                fallback_data = {
                    key: value
                    for key, value in assignment_data.items()
                    if key not in {"can_generate", "can_moderate"}
                }
                result = assignment_table.insert(fallback_data).execute()
        if not result.data:
            raise RuntimeError("Subject assignment returned no record.")
        return jsonify(
            {
                "success": True,
                "message": "Subject responsibilities saved successfully.",
                "assignment": {
                    "faculty_id": user_id,
                    "subject_id": subject_id,
                    "can_generate": can_generate,
                    "can_moderate": can_moderate,
                    "is_active": True,
                },
            }
        ), 200
    except APIError as exc:
        if _is_duplicate_key_error(exc):
            return _error("Subject is already assigned.", 409)
        current_app.logger.exception("Unable to assign subject to faculty")
        return _error("Unable to assign subject.", 500)
    except Exception:
        current_app.logger.exception("Unable to assign subject to faculty")
        return _error("Unable to assign subject.", 500)


@faculty_bp.route(
    "/api/admin/faculty/<int:user_id>/assignments", methods=["GET"]
)
@require_supabase_admin
def get_faculty_assignments_endpoint(user_id: int):
    try:
        client = db.get_supabase_admin_client()
        faculty = (
            client.table("User")
            .select("user_id")
            .eq("user_id", user_id)
            .eq("role", "faculty")
            .limit(1)
            .execute()
        ).data
        if not faculty:
            return _error("Faculty account not found.", 404)
        assignments = _fetch_faculty_assignments(
            client,
            faculty_id=user_id,
            active_only=None,
        )
        subject_ids = list({item["subject_id"] for item in assignments})
        subjects = []
        if subject_ids:
            subjects = (
                client.table("subject")
                .select("subject_id, subject_name, subject_code, branch, semester")
                .in_("subject_id", subject_ids)
                .execute()
            ).data or []
        subject_by_id = {item["subject_id"]: item for item in subjects}
        return jsonify({
            "success": True,
            "assignments": [
                {**item, "subject": subject_by_id.get(item["subject_id"])}
                for item in assignments
                if item["subject_id"] in subject_by_id
            ],
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load faculty subject assignments")
        return _error("Unable to load faculty subject assignments.", 500)


def _faculty_moderation_assignment(client, faculty_id: int, subject_id: int) -> bool:
    rows = _fetch_faculty_assignments(
        client,
        faculty_id=faculty_id,
        subject_id=subject_id,
        active_only=True,
        moderation_only=True,
        include_flags=True,
    )
    return bool(rows[:1])


def _serialize_workflow_paper(client, paper: dict) -> dict:
    subject_rows = (
        client.table("subject")
        .select("subject_name, subject_code, branch, semester")
        .eq("subject_id", paper["subject_id"])
        .limit(1)
        .execute()
    ).data or []
    generated_by_rows = []
    if paper.get("generated_by") is not None:
        generated_by_rows = (
            client.table("User")
            .select("name")
            .eq("user_id", paper["generated_by"])
            .limit(1)
            .execute()
        ).data or []
    moderated_by_rows = []
    if paper.get("moderated_by") is not None:
        moderated_by_rows = (
            client.table("User")
            .select("name")
            .eq("user_id", paper["moderated_by"])
            .limit(1)
            .execute()
        ).data or []
    raw_json = paper.get("raw_json") or {}
    selection = raw_json.get("selection") if isinstance(raw_json, dict) else None
    information = (
        selection.get("paper_information", {})
        if isinstance(selection, dict)
        else {}
    )
    subject = subject_rows[0] if subject_rows else {}
    return {
        **paper,
        "subject_name": subject.get("subject_name") or information.get("subject", ""),
        "subject_code": subject.get("subject_code") or information.get("subject_code", ""),
        "branch": subject.get("branch") or information.get("branch", ""),
        "semester": subject.get("semester") or information.get("semester", ""),
        "generated_by_name": generated_by_rows[0].get("name") if generated_by_rows else "Unknown",
        "moderated_by_name": moderated_by_rows[0].get("name") if moderated_by_rows else None,
        "paper_information": information,
        "sections": selection.get("sections", {}) if isinstance(selection, dict) else {},
    }


@faculty_bp.route("/api/faculty/moderation/subjects", methods=["GET"])
@require_supabase_roles("faculty")
def get_moderation_subjects_endpoint():
    try:
        client = db.get_supabase_admin_client()
        assignments = _fetch_faculty_assignments(
            client,
            faculty_id=g.current_user["user_id"],
            active_only=True,
            moderation_only=True,
        )
        subject_ids = list({item["subject_id"] for item in assignments})
        subjects = []
        if subject_ids:
            subjects = (
                client.table("subject")
                .select("subject_id, subject_name, subject_code, branch, semester")
                .in_("subject_id", subject_ids)
                .order("subject_name")
                .execute()
            ).data or []
        return jsonify({"success": True, "subjects": subjects}), 200
    except Exception:
        current_app.logger.exception("Unable to load moderator subject assignments")
        return _error("Unable to load moderator subject assignments.", 500)


@faculty_bp.route("/api/faculty/moderation/papers", methods=["GET"])
@require_supabase_roles("faculty")
def get_moderation_papers_endpoint():
    try:
        client = db.get_supabase_admin_client()
        assignments = _fetch_faculty_assignments(
            client,
            faculty_id=g.current_user["user_id"],
            active_only=True,
            moderation_only=True,
        )
        subject_ids = list({item["subject_id"] for item in assignments})
        if not subject_ids:
            return jsonify({"success": True, "papers": []}), 200
        papers = (
            client.table("questionpaper")
            .select("paper_id, subject_id, exam_type, exam_year, exam_date, raw_json, created_at, generated_by, status, moderated_by, moderated_at, moderation_comments")
            .in_("subject_id", subject_ids)
            .eq("status", "SUBMITTED_FOR_MODERATION")
            .execute()
        ).data or []
        eligible_papers = [
            paper for paper in papers
            if paper.get("generated_by") != g.current_user["user_id"]
        ]
        return jsonify({
            "success": True,
            "papers": [
                _serialize_workflow_paper(client, paper)
                for paper in eligible_papers
            ],
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load papers for moderation")
        return _error("Unable to load papers for moderation.", 500)


def _moderation_action(paper_id: int, status: str, comments: str | None = None):
    client = db.get_supabase_admin_client()
    paper_rows = (
        client.table("questionpaper")
        .select("paper_id, subject_id, generated_by, status")
        .eq("paper_id", paper_id)
        .limit(1)
        .execute()
    ).data or []
    if not paper_rows:
        return _error("Paper not found.", 404)
    paper = paper_rows[0]
    faculty_id = g.current_user["user_id"]
    if paper.get("generated_by") == faculty_id:
        return _error("You cannot moderate your own paper.", 403)
    if not _faculty_moderation_assignment(client, faculty_id, paper["subject_id"]):
        return _error("You are not assigned to moderate this subject.", 403)
    if paper.get("status") != "SUBMITTED_FOR_MODERATION":
        return _error("This paper is no longer awaiting moderation.", 409)
    update = {
        "status": status,
        "moderated_by": faculty_id,
        "moderated_at": datetime.now(timezone.utc).isoformat(),
        "moderation_comments": comments,
    }
    updated = (
        client.table("questionpaper")
        .update(update)
        .eq("paper_id", paper_id)
        .eq("status", "SUBMITTED_FOR_MODERATION")
        .execute()
    ).data or []
    if not updated:
        return _error("This paper is no longer awaiting moderation.", 409)
    return jsonify({"success": True, "paper": updated[0]}), 200


@faculty_bp.route(
    "/api/faculty/moderation/papers/<int:paper_id>/approve", methods=["POST"]
)
@require_supabase_roles("faculty")
def approve_moderated_paper_endpoint(paper_id: int):
    try:
        return _moderation_action(paper_id, "APPROVED_BY_MODERATOR")
    except Exception:
        current_app.logger.exception("Unable to approve moderated paper")
        return _error("Unable to approve paper.", 500)


@faculty_bp.route(
    "/api/faculty/moderation/papers/<int:paper_id>/request-changes",
    methods=["POST"],
)
@require_supabase_roles("faculty")
def request_paper_changes_endpoint(paper_id: int):
    data = request.get_json(silent=True)
    comment = data.get("comment") if isinstance(data, dict) else None
    if not isinstance(comment, str) or not comment.strip():
        return _error("A moderation comment is required.", 400)
    try:
        return _moderation_action(
            paper_id, "CHANGES_REQUESTED", comment.strip()
        )
    except Exception:
        current_app.logger.exception("Unable to request paper changes")
        return _error("Unable to request changes.", 500)


@faculty_bp.route("/api/faculty/my-papers", methods=["GET"])
@require_supabase_roles("faculty")
def get_my_papers_endpoint():
    try:
        client = db.get_supabase_admin_client()
        papers = (
            client.table("questionpaper")
            .select("paper_id, subject_id, exam_type, exam_year, exam_date, raw_json, created_at, generated_by, status, moderated_by, moderated_at, moderation_comments, reviewed_by, reviewed_at, review_comments")
            .eq("generated_by", g.current_user["user_id"])
            .order("created_at", desc=True)
            .execute()
        ).data or []
        return jsonify({
            "success": True,
            "papers": [
                _serialize_workflow_paper(client, paper)
                for paper in papers
            ],
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load faculty-generated papers")
        return _error("Unable to load your papers.", 500)


@faculty_bp.route("/api/admin/review-papers", methods=["GET"])
@require_supabase_admin
def get_admin_review_papers_endpoint():
    try:
        client = db.get_supabase_admin_client()
        papers = (
            client.table("questionpaper")
            .select("paper_id, subject_id, exam_type, exam_year, exam_date, raw_json, created_at, generated_by, status, moderated_by, moderated_at, moderation_comments, reviewed_by, reviewed_at, review_comments")
            .in_(
                "status",
                ["APPROVED_BY_MODERATOR", "SUBMITTED_FOR_ADMIN_REVIEW", "UNDER_ADMIN_REVIEW"],
            )
            .order("created_at", desc=True)
            .execute()
        ).data or []
        return jsonify({
            "success": True,
            "papers": [
                _serialize_workflow_paper(client, paper)
                for paper in papers
            ],
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load papers for admin review")
        return _error("Unable to load papers for admin review.", 500)


@faculty_bp.route(
    "/api/admin/review-papers/<int:paper_id>/finalize", methods=["POST"]
)
@require_supabase_admin
def finalize_admin_review_paper_endpoint(paper_id: int):
    data = request.get_json(silent=True)
    comment = data.get("comment", "") if isinstance(data, dict) else ""
    if not isinstance(comment, str):
        return _error("Invalid review comment.", 400)
    try:
        client = db.get_supabase_admin_client()
        result = (
            client.table("questionpaper")
            .update({
                "status": "FINALIZED",
                "reviewed_by": g.current_user["user_id"],
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "review_comments": comment.strip() or None,
            })
            .eq("paper_id", paper_id)
            .in_(
                "status",
                ["APPROVED_BY_MODERATOR", "SUBMITTED_FOR_ADMIN_REVIEW", "UNDER_ADMIN_REVIEW"],
            )
            .execute()
        ).data or []
        if not result:
            return _error("Paper not found or not awaiting admin review.", 404)
        return jsonify({"success": True, "paper": result[0]}), 200
    except Exception:
        current_app.logger.exception("Unable to finalize paper")
        return _error("Unable to finalize paper.", 500)
