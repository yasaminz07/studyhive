import os
import psycopg2
import sqlite3

def get_db_connection():
    url = os.getenv("DATABASE_URL")

    if url:
        # Production / Neon (PostgreSQL)
        return psycopg2.connect(url, sslmode="require")
    else:
        # Local dev fallback (SQLite)
        db_path = os.getenv("LOCAL_DB_PATH", "local.db")
        return sqlite3.connect(db_path)


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_reports (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        resolved BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
