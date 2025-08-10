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
        description TEXT,
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
        INSERT INTO jobs (title, company, location, applicants, link, description, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            job['title'],
            job['company'],
            job['location'],
            job['applicants'],
            job['link'],
            job['description'],
            job['status']  # 新增status字段
        ))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # 链接重复，跳过
    conn.close()

if __name__ == "__main__":
    init_db()
