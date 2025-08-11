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
        job_id TEXT,              -- 新增：LinkedIn职位ID
        description TEXT,
        html TEXT,
        is_match INTEGER,         -- 1 符合, 0 不符合
        reject_reason TEXT,       -- 不符合原因
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
            job.get('title', ''),
            job.get('company', ''),
            job.get('location', ''),
            job.get('applicants', ''),
            job.get('link', ''),
            job.get('job_id', ''),  # 新增：职位ID
            job.get('description', ''),
            job.get('html', ''),
            1 if job.get('is_match', True) else 0,
            job.get('reject_reason', ''),
            job.get('status', 'new')
        ))
        conn.commit()
        print(f"成功保存职位: {job.get('title', '')}")
        return True
    except sqlite3.IntegrityError:
        print(f"职位已存在，跳过: {job.get('title', '')}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
