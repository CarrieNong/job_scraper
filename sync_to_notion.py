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
    cursor.execute("SELECT id, title, company, location, applicants, link, job_id, description, status FROM jobs WHERE is_match=1")
    jobs = cursor.fetchall()

    def find_notion_page_by_job_id(job_id):
        """用 Notion API 查找是否已有该 job_id 的条目"""
        query = {
            "filter": {
                "property": "job_id",
                "rich_text": {
                    "equals": job_id
                }
            }
        }
        response = notion.databases.query(database_id=DATABASE_ID, **query)
        results = response.get('results')
        if results:
            return results[0]  # 返回找到的第一个条目
        return None

    for job in jobs:
        job_id, title, company, location, applicants, link, linkedin_job_id, description, status = job
        
        # 2. 检查是否已存在 Notion
        existing_page = find_notion_page_by_job_id(linkedin_job_id)
        if existing_page:
            print(f"岗位 {title} (ID: {linkedin_job_id}) 已存在 Notion，跳过")
            continue
        
        # 3. 新增岗位到 Notion
        # 处理描述字段，确保不超过 Notion 的 2000 字符限制
        description_text = description or ""
        original_length = len(description_text)
        
        print(f"岗位 {title} 的原始描述长度: {original_length} 字符")
        
        if original_length > 2000:
            # 更严格的截断：预留更多空间给省略号
            max_length = 1990  # 预留10个字符给省略号
            description_text = description_text[:max_length] + "..."
            print(f"岗位 {title} 的描述过长，已截断到 {len(description_text)} 字符")
        
        # 最终验证：如果还是超过2000，强制截断
        final_length = len(description_text)
        if final_length > 2000:
            print(f"⚠️ 警告：岗位 {title} 的描述仍然过长 ({final_length} 字符)，强制截断")
            # 强制截断到1990字符
            description_text = description_text[:1990] + "..."
            final_length = len(description_text)
            print(f"强制截断后长度: {final_length} 字符")
        
        # 最终确认长度
        if final_length > 2000:
            print(f"❌ 错误：岗位 {title} 的描述长度仍然超过2000字符 ({final_length})，跳过此岗位")
            continue
        
        print(f"岗位 {title} 的最终描述长度: {final_length} 字符")
        
        new_page = {
            "parent": {"database_id": DATABASE_ID},
            "properties": {
                "职位名称": {"title": [{"text": {"content": title}}]},
                "公司": {"rich_text": [{"text": {"content": company}}]},
                "地点": {"rich_text": [{"text": {"content": location}}]},
                "申请人数": {"rich_text": [{"text": {"content": applicants or ""}}]},
                "link": {"url": link},
                "job_id": {"rich_text": [{"text": {"content": linkedin_job_id}}]},  # 新增：保存LinkedIn职位ID
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
