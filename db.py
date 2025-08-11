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
            job['status']
        ))
        conn.commit()
        print(f"成功保存职位: {job['title']}")
        return True
    except sqlite3.IntegrityError:
        print(f"职位已存在，跳过: {job['title']}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
