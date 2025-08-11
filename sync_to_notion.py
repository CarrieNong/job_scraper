import sqlite3
from notion_client import Client
import os
from dotenv import load_dotenv

def sync_jobs_to_notion():

    load_dotenv()  # 读取.env文件

    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    DATABASE_ID = os.getenv("DATABASE_ID")

    notion = Client(auth=NOTION_TOKEN)
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()

    # 1. 查询符合条件且未同步岗位
    cursor.execute("SELECT id, title, company, location, applicants, link, description, status FROM jobs WHERE is_match=1")
    jobs = cursor.fetchall()

    def find_notion_page_by_link(link):
        """用 Notion API 查找是否已有 link 的条目"""
        query = {
            "filter": {
                "property": "link",
                "url": {
                    "equals": link
                }
            }
        }
        response = notion.databases.query(database_id=DATABASE_ID, **query)
        results = response.get('results')
        if results:
            return results[0]  # 返回找到的第一个条目
        return None

    for job in jobs:
        job_id, title, company, location, applicants, link, description, status = job
        
        # 2. 检查是否已存在 Notion
        existing_page = find_notion_page_by_link(link)
        if existing_page:
            print(f"岗位 {title} 已存在 Notion，跳过")
            continue
        
        # 3. 新增岗位到 Notion
        # 处理描述字段，确保不超过 Notion 的 2000 字符限制
        description_text = description or ""
        if len(description_text) > 2000:
            description_text = description_text[:1997] + "..."  # 保留前1997字符 + "..."
            print(f"岗位 {title} 的描述过长，已截断到2000字符")
        
        new_page = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "职位名称": {"title": [{"text": {"content": title}}]},
                "公司": {"rich_text": [{"text": {"content": company}}]},
                "地点": {"rich_text": [{"text": {"content": location}}]},
                "申请人数": {"rich_text": [{"text": {"content": applicants or ""}}]},
                "link": {"url": link},
                "描述": {"rich_text": [{"text": {"content": description_text}}]},
                # 你数据库字段对应的Notion字段，按需补充
            }
        }
        
        response = notion.pages.create(**new_page)
        print(f"新增岗位 {title} 到 Notion")
        
        # 4. 更新 SQLite 状态，标记已同步
        cursor.execute("UPDATE jobs SET status='synced' WHERE id=?", (job_id,))

    conn.commit()
    conn.close()

if __name__ == "__main__":
    sync_jobs_to_notion()
