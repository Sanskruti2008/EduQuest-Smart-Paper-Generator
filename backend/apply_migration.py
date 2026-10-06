"""
Apply SQL migration to add `parent_topic_id` to the `topic` table.

Usage:
  - Set the environment variable `DATABASE_URL` to your Postgres connection URL
    (e.g. provided by Supabase: postgres://...)
  - Run: `python apply_migration.py`

This script requires `psycopg2-binary`:
  pip install psycopg2-binary

It will execute the SQL in `migrations/20260518_link_curriculum_topics.sql`.
"""
import os
import sys

SQL_PATH = os.path.join(os.path.dirname(__file__), "migrations", "20260518_link_curriculum_topics.sql")

def main():
    db_url = os.environ.get("DATABASE_URL") or os.environ.get("SUPABASE_DB_URL")
    if not db_url:
        print("ERROR: set DATABASE_URL or SUPABASE_DB_URL environment variable to your Postgres URL")
        sys.exit(1)

    try:
        import psycopg2
    except ImportError:
        print("Please install psycopg2-binary: pip install psycopg2-binary")
        sys.exit(1)

    if not os.path.exists(SQL_PATH):
        print(f"Migration file not found: {SQL_PATH}")
        sys.exit(1)

    with open(SQL_PATH, "r", encoding="utf-8") as f:
        sql = f.read()

    try:
        conn = psycopg2.connect(db_url)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        conn.close()
        print("Migration applied successfully.")
    except Exception as e:
        print(f"Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
