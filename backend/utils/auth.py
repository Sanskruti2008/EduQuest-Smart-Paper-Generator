import os
import secrets
from functools import wraps

from dotenv import load_dotenv
from flask import current_app, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from supabase_auth.errors import AuthApiError, AuthInvalidJwtError

import database as db

load_dotenv()

ADMIN_AUTH_SECRET = os.getenv("ADMIN_AUTH_SECRET") or secrets.token_urlsafe(32)
ADMIN_TOKEN_TTL_SECONDS = int(os.getenv("ADMIN_TOKEN_TTL", "43200"))
_admin_serializer = URLSafeTimedSerializer(ADMIN_AUTH_SECRET)


def _generate_role_token(username: str, role: str) -> str:
    return _admin_serializer.dumps({"sub": username, "role": role}, salt="admin-auth")


def _verify_admin_token(token: str) -> dict:
    return _admin_serializer.loads(
        token, salt="admin-auth", max_age=ADMIN_TOKEN_TTL_SECONDS
    )


def get_supabase_auth_user_id(token: str) -> str | None:
    try:
        auth_response = db.get_supabase_admin_client().auth.get_user(token)
    except AuthInvalidJwtError:
        return None
    except AuthApiError as exc:
        if exc.status < 500:
            return None
        raise

    auth_user = auth_response.user if auth_response else None
    auth_user_id = getattr(auth_user, "id", None)
    return str(auth_user_id) if auth_user_id else None


def get_supabase_profile_for_auth_user(auth_user_id: str) -> dict | None:
    result = (
        db.get_supabase_admin_client()
        .table("User")
        .select(
            "user_id, auth_user_id, name, role, email, employee_id, department, is_active"
        )
        .eq("auth_user_id", auth_user_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def get_supabase_profile(token: str) -> dict | None:
    auth_user_id = get_supabase_auth_user_id(token)
    if not auth_user_id:
        return None
    return get_supabase_profile_for_auth_user(auth_user_id)


def _extract_bearer_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return ""


def _authentication_service_unavailable():
    current_app.logger.exception("Unable to validate Supabase access token")
    return jsonify(
        {"success": False, "message": "Authentication service unavailable."}
    ), 503


def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = _extract_bearer_token()
            if not token:
                token = request.headers.get("X-Admin-Token", "").strip()
            if not token:
                return jsonify({"error": "Authorization required"}), 401

            try:
                payload = _verify_admin_token(token)
            except SignatureExpired:
                return jsonify({"error": "Authorization token expired"}), 401
            except BadSignature:
                try:
                    profile = get_supabase_profile(token)
                except Exception:
                    return _authentication_service_unavailable()
                if not profile:
                    return jsonify({"error": "Invalid authorization token"}), 401
                role = str(profile.get("role", "")).lower()
                if not profile.get("is_active", True) or role not in allowed_roles:
                    return jsonify({"error": "Insufficient privileges"}), 403
                g.current_user = profile
                return func(*args, **kwargs)

            if payload.get("role") not in allowed_roles:
                return jsonify({"error": "Insufficient privileges"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_supabase_admin(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify(
                {"success": False, "message": "Authentication required."}
            ), 401
        try:
            profile = get_supabase_profile(token)
        except Exception:
            return _authentication_service_unavailable()
        if not profile:
            return jsonify(
                {"success": False, "message": "Authentication required."}
            ), 401
        if (
            str(profile.get("role", "")).lower() != "admin"
            or not profile.get("is_active", True)
        ):
            return jsonify(
                {"success": False, "message": "Admin access required."}
            ), 403
        g.current_user = profile
        return func(*args, **kwargs)

    return wrapper


def require_supabase_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = _extract_bearer_token()
            if not token:
                return jsonify({"error": "Authorization required"}), 401
            try:
                profile = get_supabase_profile(token)
            except Exception:
                return _authentication_service_unavailable()
            if not profile:
                return jsonify({"error": "Invalid authorization token"}), 401
            role = str(profile.get("role", "")).lower()
            if not profile.get("is_active", True) or role not in allowed_roles:
                return jsonify({"error": "Insufficient privileges"}), 403
            g.current_user = profile
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_supabase_faculty_profile(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({
                "success": False,
                "message": "Authentication required.",
            }), 401
        try:
            auth_user_id = get_supabase_auth_user_id(token)
        except Exception:
            return _authentication_service_unavailable()
        if not auth_user_id:
            current_app.logger.info(
                "Faculty profile authentication rejected (authorization_header_present=true)"
            )
            return jsonify({
                "success": False,
                "message": "Authentication required.",
            }), 401

        try:
            profile = get_supabase_profile_for_auth_user(auth_user_id)
        except Exception:
            current_app.logger.exception(
                "Unable to load the public faculty profile (auth_user_id=%s)",
                auth_user_id,
            )
            return jsonify({
                "success": False,
                "message": "Unable to load faculty profile.",
            }), 500

        if not profile:
            current_app.logger.warning(
                "Authenticated Supabase user has no public.User profile "
                "(auth_user_id=%s, profile_found=false)",
                auth_user_id,
            )
            return jsonify({
                "success": False,
                "message": (
                    "Faculty profile is not linked to this authentication account."
                ),
            }), 404

        role = str(profile.get("role", "")).lower()
        is_active = bool(profile.get("is_active", True))
        current_app.logger.info(
            "Faculty profile resolved (auth_user_id=%s, profile_found=true, role=%s, is_active=%s)",
            auth_user_id,
            role,
            is_active,
        )
        if role != "faculty":
            return jsonify({
                "success": False,
                "message": "Faculty access required.",
            }), 403
        if not is_active:
            return jsonify({
                "success": False,
                "message": "Faculty account is inactive.",
            }), 403

        g.current_user = profile
        return func(*args, **kwargs)

    return wrapper


def require_admin(func):
    return require_roles("admin")(func)
