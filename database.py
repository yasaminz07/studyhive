import os
import psycopg2
import sqlite3

def get_db_connection():
    database_url = os.getenv("DATABASE_URL")

    # If DATABASE_URL exists → use Neon (Postgres)
    if database_url:
        return psycopg2.connect(database_url)

    # Otherwise → use local SQLite
    db_path = os.getenv("LOCAL_DB_PATH", "local.db")
    return sqlite3.connect(db_path)


def init_db():
    # Only create tables for SQLite (local dev)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return  # Do nothing on Neon

    conn = sqlite3.connect(os.getenv("LOCAL_DB_PATH", "local.db"))
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            resolved BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
