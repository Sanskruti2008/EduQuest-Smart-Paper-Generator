import os
import secrets
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from dotenv import load_dotenv
load_dotenv()

ADMIN_AUTH_SECRET = os.getenv('ADMIN_AUTH_SECRET') or secrets.token_urlsafe(32)
ADMIN_TOKEN_TTL_SECONDS = int(os.getenv('ADMIN_TOKEN_TTL', '43200'))
_admin_serializer = URLSafeTimedSerializer(ADMIN_AUTH_SECRET)

def _generate_role_token(username: str, role: str) -> str:
    return _admin_serializer.dumps({"sub": username, "role": role}, salt='admin-auth')


def _generate_admin_token(username: str) -> str:
    return _generate_role_token(username, "admin")

def _verify_admin_token(token: str) -> dict:
    return _admin_serializer.loads(token, salt='admin-auth', max_age=ADMIN_TOKEN_TTL_SECONDS)

from flask import request, jsonify
from functools import wraps

def require_roles(*allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth_header = request.headers.get('Authorization', '')
            token = ''
            if auth_header.lower().startswith('bearer '):
                token = auth_header.split(' ', 1)[1].strip()
            if not token:
                token = request.headers.get('X-Admin-Token', '').strip()
            if not token:
                return jsonify({'error': 'Authorization required'}), 401
            try:
                payload = _verify_admin_token(token)
            except SignatureExpired:
                return jsonify({'error': 'Authorization token expired'}), 401
            except BadSignature:
                return jsonify({'error': 'Invalid authorization token'}), 401
            if payload.get('role') not in allowed_roles:
                return jsonify({'error': 'Insufficient privileges'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_admin(func):
    return require_roles('admin')(func)
