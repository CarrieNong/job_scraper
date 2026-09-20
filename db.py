# db.py
import sqlite3

DB_NAME = "jobs.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT,
        applicants TEXT,
        link TEXT UNIQUE,
        job_id TEXT,
        description TEXT,
        source TEXT DEFAULT 'linkedin',
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("PRAGMA table_info(jobs)")
    columns = {row[1] for row in cursor.fetchall()}
    if "source" not in columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN source TEXT DEFAULT 'linkedin'")
        cursor.execute("UPDATE jobs SET source = 'linkedin' WHERE source IS NULL OR source = ''")
    conn.commit()
    conn.close()


def save_job(job):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO jobs (title, company, location, applicants, link, job_id, description, source, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("applicants", ""),
            job.get("link", ""),
            job.get("job_id", ""),
            job.get("description", ""),
            job.get("source", "linkedin"),
            job.get("status", "new"),
        ))
        conn.commit()
        print(f"Saved job: {job.get('title', '')}")
        return True
    except sqlite3.IntegrityError:
        print(f"Job already exists, skip: {job.get('title', '')}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
