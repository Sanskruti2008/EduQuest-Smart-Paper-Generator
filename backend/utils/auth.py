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


def get_supabase_profile(token: str) -> dict | None:
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
    if not auth_user_id:
        return None

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


def require_admin(func):
    return require_roles("admin")(func)
