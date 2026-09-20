# Project Structure - 项目结构说明

## Overview - 概览

The project has been reorganized for better maintainability:
- All Python source files are in `src/` directory
- Configuration and profile files are in `docs/` directory  
- All documentation is consolidated into a single `README.md`
- All code comments are in English

项目已重组以提高可维护性：
- 所有Python源文件在 `src/` 目录
- 配置和个人资料文件在 `docs/` 目录
- 所有文档已合并到单个 `README.md`
- 所有代码注释使用英文

## Directory Structure - 目录结构

```
job_scraper/
├── src/                        # Python source files - Python源文件
│   ├── ai_matcher.py          # AI-powered job matching engine - AI匹配引擎
│   ├── config.py              # Central configuration - 集中配置
│   ├── db_mongo.py            # MongoDB operations - MongoDB操作
│   ├── indeed_scraper.py      # Indeed scraper - Indeed爬虫
│   ├── linkedin_scraper.py    # LinkedIn scraper - LinkedIn爬虫
│   └── scraper_utils.py       # Shared utility functions - 共享工具函数
│
├── docs/                       # Configuration & profile files - 配置和个人资料
│   ├── user_profile.md        # Your resume/profile (required for AI) - 你的简历
│   └── matching_criteria.md   # Job matching criteria (required for AI) - 匹配标准
│
├── run_task.sh                # Automated execution script - 自动化执行脚本
├── com.user.job_scraper.plist # macOS LaunchD configuration - macOS定时任务配置
├── requirements.txt           # Python dependencies - Python依赖
├── .env                       # Environment variables (not in git) - 环境变量
├── .gitignore                 # Git ignore rules - Git忽略规则
└── README.md                  # Complete documentation - 完整文档
```

## Usage - 使用方法

### Running Scripts - 运行脚本

All scripts must be run from the project root directory:
所有脚本必须从项目根目录运行：

```bash
# Scrape jobs - 爬取岗位
python3 src/indeed_scraper.py -k "frontend" -p 1
python3 src/linkedin_scraper.py -k "backend" -p 1

# AI matching - AI匹配
python3 src/ai_matcher.py -l 5

# Complete pipeline - 完整流程
./run_task.sh
```

### Editing Configuration - 编辑配置

```bash
# Edit your profile - 编辑个人资料
vim docs/user_profile.md

# Edit matching criteria - 编辑匹配标准
vim docs/matching_criteria.md

# Edit search keywords - 编辑搜索关键词
vim src/config.py

# Edit environment variables - 编辑环境变量
vim .env
```

## File Paths - 文件路径

### Updated Paths - 更新的路径

The following paths have been updated in the code:
以下路径已在代码中更新：

| Old Path 旧路径 | New Path 新路径 | File 文件 |
|----------------|----------------|----------|
| `user_profile.md` | `docs/user_profile.md` | `src/ai_matcher.py` |
| `matching_criteria.txt` | `docs/matching_criteria.md` | `src/ai_matcher.py` |
| `indeed_scraper.py` | `src/indeed_scraper.py` | `run_task.sh` |
| `linkedin_scraper.py` | `src/linkedin_scraper.py` | `run_task.sh` |
| `ai_matcher.py` | `src/ai_matcher.py` | `run_task.sh` |

### Python Imports - Python导入

All Python files in `src/` can import each other directly:
`src/`目录下的所有Python文件可以直接相互导入：

```python
from config import DEFAULT_KEYWORDS
from db_mongo import init_db, save_job
from scraper_utils import wait_for_page_load
```

No changes are needed to import statements.
导入语句无需修改。

## Removed Files - 已删除文件

The following documentation files have been merged into `README.md`:
以下文档文件已合并到 `README.md`：

- ❌ `AI_MATCHING_GUIDE.md` → Merged into README - 已合并到README
- ❌ `UPDATE_SUMMARY.md` → Merged into README - 已合并到README
- ❌ `QUICKSTART.md` → Merged into README - 已合并到README
- ❌ `SCHEDULING.md` → Merged into README - 已合并到README

All information is now in the comprehensive `README.md`.
所有信息现在都在综合的 `README.md` 中。

## Migration Notes - 迁移说明

### If You Have Existing Scripts - 如果你有现有脚本

If you have custom scripts that reference the old paths, update them:
如果你有引用旧路径的自定义脚本，请更新它们：

```bash
# Old - 旧的
python3 indeed_scraper.py

# New - 新的
python3 src/indeed_scraper.py
```

### If You Use Absolute Imports - 如果你使用绝对导入

For external scripts that import from this project:
对于从此项目导入的外部脚本：

```python
# Old - 旧的
from job_scraper.config import DEFAULT_KEYWORDS

# New - 新的
from job_scraper.src.config import DEFAULT_KEYWORDS
```

## Benefits - 优势

✅ **Better Organization** - Separate source code from configuration
   **更好的组织** - 源代码与配置分离

✅ **Single Documentation** - All info in one place (README.md)
   **单一文档** - 所有信息集中在一处 (README.md)

✅ **English Comments** - All code comments are in English for better collaboration
   **英文注释** - 所有代码注释使用英文，便于协作

✅ **Cleaner Root** - Less clutter in project root directory
   **更清爽的根目录** - 项目根目录更整洁

✅ **Easier Maintenance** - Clear separation of concerns
   **更易维护** - 清晰的关注点分离

## Next Steps - 下一步

1. ✅ Structure reorganized - 结构已重组
2. ✅ Documentation consolidated - 文档已整合
3. ✅ Comments translated to English - 注释已翻译为英文
4. 📝 Update your `.env` file if needed - 如需要，更新 `.env` 文件
5. 📝 Edit `docs/user_profile.md` with your information - 编辑个人资料
6. 🧪 Test the scripts - 测试脚本

```bash
# Test scraper - 测试爬虫
python3 src/indeed_scraper.py -k "frontend" -p 1

# Test AI matcher - 测试AI匹配
python3 src/ai_matcher.py -l 3

# Test complete pipeline - 测试完整流程
./run_task.sh
```

---

**Note**: All changes are backward compatible with existing data in MongoDB.
**注意**：所有更改都与MongoDB中的现有数据向后兼容。

For complete documentation, see [README.md](README.md).
完整文档请查看 [README.md](README.md)。
