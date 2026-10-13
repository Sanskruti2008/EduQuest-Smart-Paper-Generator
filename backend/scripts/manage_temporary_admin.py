"""Create or revoke a random Supabase admin account for local testing."""

import argparse
import json
import secrets
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
CREDENTIALS_FILE = BACKEND_DIR / ".temporary-admin-credentials.json"
load_dotenv(BACKEND_DIR / ".env", override=True)
sys.path.insert(0, str(BACKEND_DIR))

import database as db


def create_temporary_admin() -> None:
    if CREDENTIALS_FILE.exists():
        raise RuntimeError(
            f"{CREDENTIALS_FILE.name} already exists. Revoke that account first."
        )

    client = db.get_supabase_admin_client()
    suffix = secrets.token_hex(8)
    email = f"temp-admin-{suffix}@example.com"
    password = secrets.token_urlsafe(24)
    auth_user_id = None
    profile = None
    try:
        auth_response = client.auth.admin.create_user(
            {
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"name": "Temporary Test Admin"},
            }
        )
        auth_user_id = getattr(auth_response.user, "id", None)
        if not auth_user_id:
            raise RuntimeError("Supabase did not return the created user's ID.")

        profile = {
            "auth_user_id": auth_user_id,
            "name": "Temporary Test Admin",
            "role": "admin",
            "email": email,
            "is_active": True,
        }
        result = client.table("User").insert(profile).execute()
        if not result.data:
            raise RuntimeError("The admin profile insert returned no record.")

        credentials = {
            "purpose": "temporary-admin-test",
            "email": email,
            "password": password,
            "auth_user_id": auth_user_id,
        }
        with CREDENTIALS_FILE.open("x", encoding="utf-8") as credential_file:
            json.dump(credentials, credential_file, indent=2)
            credential_file.write("\n")
    except Exception:
        if auth_user_id:
            if profile:
                try:
                    (
                        client.table("User")
                        .update({"is_active": False})
                        .eq("auth_user_id", auth_user_id)
                        .execute()
                    )
                except Exception:
                    print("Could not deactivate the partially created admin profile.")
            try:
                client.auth.admin.delete_user(auth_user_id)
            except Exception:
                print("Could not remove the partially created Supabase Auth user.")
        raise

    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"Credentials saved locally in {CREDENTIALS_FILE.name} (git-ignored).")


def revoke_temporary_admin() -> None:
    if not CREDENTIALS_FILE.is_file():
        raise RuntimeError("No local temporary-admin credentials file was found.")

    credentials = json.loads(CREDENTIALS_FILE.read_text(encoding="utf-8"))
    if credentials.get("purpose") != "temporary-admin-test":
        raise RuntimeError("Refusing to revoke an unrecognized account record.")
    auth_user_id = credentials.get("auth_user_id")
    if not isinstance(auth_user_id, str) or not auth_user_id:
        raise RuntimeError("The local account record has no Supabase user ID.")

    client = db.get_supabase_admin_client()
    (
        client.table("User")
        .update({"is_active": False})
        .eq("auth_user_id", auth_user_id)
        .eq("role", "admin")
        .execute()
    )
    client.auth.admin.delete_user(auth_user_id)
    CREDENTIALS_FILE.unlink()
    print("Temporary admin access revoked and local credentials removed.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("create", "revoke"))
    action = parser.parse_args().action
    if action == "create":
        create_temporary_admin()
    else:
        revoke_temporary_admin()


if __name__ == "__main__":
    main()
