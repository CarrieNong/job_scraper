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
        html TEXT,
        is_match INTEGER,
        reject_reason TEXT,
        status TEXT DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()


def save_job(job):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO jobs (title, company, location, applicants, link, job_id, description, html, is_match, reject_reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            job.get("title", ""),
            job.get("company", ""),
            job.get("location", ""),
            job.get("applicants", ""),
            job.get("link", ""),
            job.get("job_id", ""),
            job.get("description", ""),
            job.get("html", ""),
            job.get("is_match"),
            job.get("reject_reason", ""),
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
