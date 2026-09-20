# Quick Start Guide - 快速开始

## ✅ 已完成的功能

你的项目现在包含以下完整功能：

### 1. 岗位爬取 (Job Scraping)
- ✅ Indeed 爬虫 (`indeed_scraper.py`)
- ✅ LinkedIn 爬虫 (`linkedin_scraper.py`)
- ✅ MongoDB 数据存储 (`db_mongo.py`)

### 2. AI 智能匹配 (NEW!)
- ✅ AI 岗位分析器 (`ai_matcher.py`)
- ✅ 自动评分系统 (0-10 分)
- ✅ 匹配原因分析
- ✅ 独立的 matched_jobs 数据表

### 3. 自动化任务 (NEW!)
- ✅ 自动化运行脚本 (`run_task.sh`)
- ✅ macOS LaunchD 配置 (`com.user.job_scraper.plist`)
- ✅ Cron 定时任务支持

## 🚀 立即开始使用

### 第一步：安装依赖

```bash
cd /Users/carrienon/Desktop/code-project/job_scraper
pip install -r requirements.txt
playwright install chromium
```

### 第二步：配置 API Key

编辑 `.env` 文件，添加你的 OpenAI API Key：

```bash
OPENAI_API_KEY=sk-proj-你的密钥
AI_MODEL=gpt-4o-mini
MATCH_THRESHOLD=7.0
```

**获取 API Key：** https://platform.openai.com/api-keys

💰 **费用参考：**
- gpt-4o-mini: 分析 100 个岗位约 $0.10-0.30 (推荐)
- gpt-4o: 分析 100 个岗位约 $2-5

### 第三步：填写你的简历和要求

1. **编辑 `user_profile.md`** - 填写你的技能、经验、期望
2. **编辑 `matching_criteria.txt`** - 填写你的硬性要求和偏好

模板已经创建好了，只需要替换成你的信息即可！

### 第四步：测试运行

```bash
# 1. 测试爬虫（只爬 1 页）
python3 indeed_scraper.py -k "frontend" -p 1

# 2. 测试 AI 匹配（只分析 3 个岗位）
python3 ai_matcher.py -l 3

# 3. 查看匹配结果
python3 view_matches.py --top
```

### 第五步：设置定时任务

每天自动运行：

```bash
# 复制配置文件
cp com.user.job_scraper.plist ~/Library/LaunchAgents/

# 加载定时任务（每天早上 9 点运行）
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist

# 立即测试一次
launchctl start com.user.job_scraper
```

## 📖 常用命令

### 爬取岗位

```bash
# 爬取 Indeed（默认关键词，2 页）
python3 indeed_scraper.py -p 2

# 爬取 LinkedIn（指定关键词）
python3 linkedin_scraper.py -k "python developer" "full stack" -p 2
```

### AI 匹配

```bash
# 分析所有新岗位
python3 ai_matcher.py

# 只分析 LinkedIn 的岗位
python3 ai_matcher.py -s linkedin

# 提高匹配门槛（只保存 8 分以上）
python3 ai_matcher.py -t 8.0
```

### 查看匹配结果

直接在 MongoDB 中查看 `matched_jobs` 集合：

**使用 Python:**
```python
from db_mongo import init_db, get_collection

init_db()

# 查看所有匹配的岗位，按分数排序
matched = get_collection("matched_jobs")
jobs = matched.find().sort("match_score", -1)

for job in jobs:
    print(f"{job['match_score']}/10 - {job['title']} at {job['company']}")
    print(f"  Link: {job['link']}")
    print(f"  Reasons: {', '.join(job['match_reasons'])}\n")
```

**使用 MongoDB Compass:**
1. 打开 MongoDB Compass
2. 连接到你的数据库
3. 浏览 `matched_jobs` 集合
4. 按 `match_score` 降序排列

### 完整流程

```bash
# 一键运行：爬取 + AI 匹配 + 日志
./run_task.sh
```

## 📊 查看数据库

### 使用 Python

```python
from db_mongo import init_db, get_collection

init_db()

# 查看所有匹配的岗位
matched = get_collection("matched_jobs")
jobs = matched.find().sort("match_score", -1)

for job in jobs:
    print(f"{job['match_score']}/10 - {job['title']}")
```

### 使用 MongoDB Compass

1. 下载安装：https://www.mongodb.com/products/compass
2. 连接到你的数据库
3. 浏览 `job_scraper` 数据库
4. 查看 `jobs` 和 `matched_jobs` 两个集合

## 🎯 推荐工作流程

### 初始设置（一次性）
1. ✅ 填写 `user_profile.txt` 和 `matching_criteria.txt`
2. ✅ 设置 `.env` 中的 API Key
3. ✅ 测试运行爬虫和匹配
4. ✅ 设置定时任务

### 每日工作流程（自动化后）
1. 🤖 系统每天自动爬取新岗位
2. 🤖 AI 自动分析并筛选匹配岗位
3. 📧 你查看 `matched_jobs` 中的推荐
4. ✅ 选择岗位投递
5. 📝 更新岗位状态（pending → applied）

### 手动查看流程
```bash
# 1. 使用 Python 查看匹配结果
python3 -c "
from db_mongo import get_collection, init_db
init_db()
matched = get_collection('matched_jobs')
for job in matched.find().sort('match_score', -1).limit(10):
    print(f\"{job['match_score']}/10 - {job['title']} at {job['company']}\")
    print(f\"  {job['link']}\n\")
"

# 2. 或使用 MongoDB Compass GUI 查看
# 连接到数据库，浏览 matched_jobs 集合

# 3. 投递后更新状态
python3 -c "
from db_mongo import get_collection, init_db
from datetime import datetime
init_db()
matched = get_collection('matched_jobs')
matched.update_one(
    {'job_id': '岗位ID', 'source': 'linkedin'},
    {'\$set': {'status': 'applied', 'applied_at': datetime.utcnow()}}
)
"
```

## 📂 文件说明

| 文件 | 用途 | 需要修改 |
|------|------|---------|
| `user_profile.md` | 你的简历和技能 | ✅ 必须 |
| `matching_criteria.txt` | 岗位要求 | ✅ 必须 |
| `.env` | API 密钥和配置 | ✅ 必须 |
| `indeed_scraper.py` | Indeed 爬虫 | ❌ 不用 |
| `linkedin_scraper.py` | LinkedIn 爬虫 | ❌ 不用 |
| `ai_matcher.py` | AI 匹配引擎 | ❌ 不用 |
| `run_task.sh` | 自动化脚本 | 可选 |
| `config.py` | 全局配置 | 可选 |

## 🐛 常见问题

### 1. API Key 错误
```
Error: AI API key not configured
```

**解决：** 检查 `.env` 文件中的 `OPENAI_API_KEY` 是否正确

### 2. 没有新岗位可分析
```
No new jobs to process.
```

**解决：** 先运行爬虫：`python3 indeed_scraper.py -p 1`

### 3. Chrome 连接失败

**解决：** 手动启动 Chrome：
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium"
```

### 4. MongoDB 连接失败

**解决：** 检查 `.env` 中的 `MONGO_URI` 是否正确

## 📚 详细文档

- **[README.md](README.md)** - 完整项目说明
- **[AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md)** - AI 匹配详细指南
- **[SCHEDULING.md](SCHEDULING.md)** - 定时任务详细配置

## 💡 高级技巧

### 调整 AI 匹配标准

如果发现匹配结果不理想：

1. **太多误报？** → 提高阈值：`MATCH_THRESHOLD=8.0`
2. **漏掉好岗位？** → 降低阈值：`MATCH_THRESHOLD=6.0`
3. **标准不对？** → 修改 `matching_criteria.txt`
4. **技能不匹配？** → 更新 `user_profile.txt`

### 多关键词搜索

在 `config.py` 中添加更多关键词：

```python
DEFAULT_KEYWORDS = [
    "frontend developer",
    "react developer",
    "vue developer",
    "full stack engineer",
    "typescript engineer",
]
```

### 按来源分析

```bash
# 只分析 Indeed 的岗位
python3 ai_matcher.py -s indeed

# 只分析 LinkedIn 的岗位
python3 ai_matcher.py -s linkedin
```

## 🎓 下一步建议

1. ✅ **今天：** 完成配置，测试运行
2. ✅ **本周：** 设置定时任务，观察匹配质量
3. ✅ **持续：** 根据结果调整匹配标准
4. 🚀 **未来：** 可以添加 Notion 同步、邮件通知等功能

## 🤝 需要帮助？

- 检查日志：`tail -f task.log`
- 查看错误：`cat stderr.log`
- 重新阅读文档中的 Troubleshooting 部分

---

**祝你早日找到心仪的工作！Good luck with your job search! 🎉**
