"""Create the PostgreSQL database referenced by DATABASE_URL in .env.

Usage:
  python scripts/create_db.py

This connects to the default `postgres` database and issues
CREATE DATABASE if the target does not exist.
"""
import os
import urllib.parse

try:
    import psycopg2
except Exception as exc:
    raise SystemExit("psycopg2 is required. Install with: pip install psycopg2-binary") from exc

from dotenv import load_dotenv


def main():
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL not set in environment/.env")

    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise SystemExit("DATABASE_URL does not look like a PostgreSQL URL: %r" % url)

    dbname = parsed.path.lstrip("/")
    user = parsed.username or os.environ.get("USER")
    password = parsed.password or os.environ.get("PGPASSWORD")
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    # Connect to the default 'postgres' database to create the target DB
    conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
    conn.autocommit = True
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (dbname,))
    if cur.fetchone():
        print(f"Database already exists: {dbname}")
    else:
        cur.execute('CREATE DATABASE "{}"'.format(dbname))
        print(f"Created database: {dbname}")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
