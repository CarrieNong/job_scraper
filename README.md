# Job Scraper

A Python-based web scraper that automatically collects job listings from Indeed and LinkedIn, stores them in MongoDB, and helps you track job opportunities efficiently.

## 🚀 Features

- **Multi-Platform Support**: Scrapes job listings from both Indeed and LinkedIn
- **AI-Powered Job Matching**: Uses OpenAI/Claude to analyze jobs and find the best matches for your profile
- **Smart Deduplication**: Automatically detects and skips duplicate job postings using job IDs
- **Human-Like Behavior**: Implements random delays and scrolling patterns to avoid detection
- **MongoDB Integration**: Stores all job data in MongoDB with flexible querying capabilities
- **Customizable Search**: Configure keywords, location, and time filters
- **Browser Automation**: Uses Playwright with Chrome DevTools Protocol for reliable scraping
- **Automated Scheduling**: Includes shell script for scheduled task execution
- **Match Scoring**: AI scores each job (0-10) based on your profile and preferences

## 📋 Prerequisites

- Python 3.8+
- Google Chrome browser
- MongoDB (local or MongoDB Atlas cloud database)

## 🛠 Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd job_scraper
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Install Playwright Browsers

```bash
playwright install chromium
```

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# MongoDB configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0

# Or use local MongoDB
# MONGO_URI=mongodb://localhost:27017/

# Optional: Database name (defaults to "job_scraper")
# DB_NAME=job_scraper

# AI Configuration (for job matching)
OPENAI_API_KEY=your_openai_api_key_here
AI_MODEL=gpt-4o-mini
MATCH_THRESHOLD=7.0
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

### 5. Set Up Your Profile (for AI Matching)

Edit `user_profile.md` (or `user_profile.txt`) with your resume and preferences:

```markdown
## Personal Information
- Name: Your Name
- Current Role: Software Engineer
- Years of Experience: 3+ years
...

## Technical Skills
- Frontend: React, Vue.js, TypeScript
- Backend: Node.js, Python
...
```

Edit `matching_criteria.txt` with your job requirements:

```text
## Must-Have Requirements
1. Position involves React or modern frameworks
2. Remote-friendly or Berlin-based
...
```

## ⚙️ Configuration

Edit `config.py` to customize scraping parameters:

```python
# Search keywords
DEFAULT_KEYWORDS = [
    "frontend",
    "full stack",
    "ai engineer",
    "software engineer",
]

# Scraping limits
DEFAULT_MAX_PAGES = 3        # Pages per keyword
MAX_JOBS_PER_PAGE = 30       # Jobs to process per page

# Chrome debugging settings
CDP_PORT = 9222              # Chrome DevTools Protocol port
```

### Indeed Configuration

```python
INDEED_CONFIG = {
    "base_url": "https://de.indeed.com/jobs",
    "fromage": "1",          # Posted within last 1 day
    "results_per_page": 10,  # Results per page
}
```

### LinkedIn Configuration

```python
LINKEDIN_CONFIG = {
    "base_url": "https://www.linkedin.com/jobs/search/",
    "geo_id": "101282230",   # Germany
    "time_filter": "r86400", # Last 24 hours
}
```

## 🎯 Usage

### 1. Scrape Job Listings

#### Run Indeed Scraper

```bash
# Use default keywords and pages
python3 indeed_scraper.py

# Specify custom keywords
python3 indeed_scraper.py --keywords "python developer" "data scientist"

# Limit pages per keyword
python3 indeed_scraper.py --max-pages 1

# Combine options (recommended for testing)
python3 indeed_scraper.py -k "frontend" -p 1
```

#### Run LinkedIn Scraper

```bash
# Use default keywords and pages
python3 linkedin_scraper.py

# Specify custom keywords
python3 linkedin_scraper.py --keywords "backend" "devops"

# Limit pages per keyword
python3 linkedin_scraper.py --max-pages 2
```

### 2. AI Job Matching (NEW!)

After scraping jobs, use AI to find the best matches:

```bash
# Analyze all new jobs
python3 ai_matcher.py

# Test with a few jobs first
python3 ai_matcher.py --limit 5

# Only process Indeed jobs
python3 ai_matcher.py --source indeed

# Set custom match threshold (0-10)
python3 ai_matcher.py --threshold 8.0
```

The AI will:
- Analyze each job against your profile
- Score each job from 0-10
- Save high-quality matches (≥7.0) to `matched_jobs` collection
- Provide reasons for each match/rejection

**See [AI_MATCHING_GUIDE.md](AI_MATCHING_GUIDE.md) for detailed setup and usage.**

### 3. Complete Pipeline

Run everything at once:

```bash
./run_task.sh
```

This will:
1. Scrape Indeed jobs
2. Scrape LinkedIn jobs  
3. Run AI matching on new jobs
4. Log all results

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keywords` | `-k` | Search keywords (space-separated) | `DEFAULT_KEYWORDS` |
| `--max-pages` | `-p` | Pages to scrape per keyword | `3` |

### Examples

```bash
# Quick test - single keyword, one page
python3 indeed_scraper.py -k "frontend" -p 1

# Multiple keywords, 2 pages each
python3 indeed_scraper.py -k "python" "javascript" "golang" -p 2

# Use keywords with spaces
python3 linkedin_scraper.py -k "machine learning" "ai engineer"
```

## 📁 Project Structure

```
job_scraper/
├── config.py                      # Central configuration for all scrapers
├── scraper_utils.py               # Shared utility functions
├── db_mongo.py                    # MongoDB database operations
├── indeed_scraper.py              # Indeed job scraper
├── linkedin_scraper.py            # LinkedIn job scraper
├── ai_matcher.py                  # AI-powered job matching (NEW!)
├── user_profile.md                # Your resume/profile (NEW!)
├── matching_criteria.txt          # Job matching criteria (NEW!)
├── run_task.sh                    # Shell script for automated execution
├── com.user.job_scraper.plist     # macOS LaunchD configuration
├── requirements.txt               # Python dependencies
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git ignore rules
├── README.md                      # This file
├── AI_MATCHING_GUIDE.md           # Detailed AI matching guide (NEW!)
└── SCHEDULING.md                  # Task scheduling guide (NEW!)
```

## 🗄 Database Schema

### Collection: `jobs`

All scraped jobs are stored here:

```json
{
  "title": "Senior Frontend Developer",
  "company": "Tech Company GmbH",
  "location": "Berlin, Germany",
  "status": "new",
  "link": "https://...",
  "job_id": "unique_job_identifier",
  "applicants": "50 applicants",
  "description": "Full HTML job description...",
  "source": "indeed",
  "created_at": "2026-09-20T19:30:00Z"
}
```

### Collection: `matched_jobs` (NEW!)

AI-analyzed jobs with high match scores:

```json
{
  "title": "Senior Frontend Developer",
  "company": "Tech Company GmbH",
  "location": "Berlin, Germany",
  "link": "https://...",
  "job_id": "unique_job_identifier",
  "source": "indeed",
  "description": "...",
  
  "match_score": 8.5,
  "recommendation": "Yes",
  "match_reasons": [
    "Strong React expertise match",
    "Remote work option available"
  ],
  "missing_requirements": ["5+ years preferred"],
  "red_flags": [],
  "summary": "Excellent match for frontend role",
  
  "status": "pending",
  "matched_at": "2026-09-20T19:30:00Z",
  "applied_at": null,
  "notes": ""
}
```

### Query Jobs

Use the MongoDB client or `db_mongo.py` functions:

```python
from db_mongo import init_db, get_jobs_by_source, count_jobs, get_collection

# Initialize database connection
init_db()

# Get all Indeed jobs
indeed_jobs = get_jobs_by_source("indeed")

# Count jobs by source
count = count_jobs("linkedin")

# Get matched jobs sorted by score
matched = get_collection("matched_jobs")
best_matches = matched.find().sort("match_score", -1).limit(10)
```

## 🤖 Automated Scheduling

Schedule the complete pipeline to run daily:

### Quick Setup (macOS LaunchD - Recommended)

```bash
# 1. Copy the plist file
cp com.user.job_scraper.plist ~/Library/LaunchAgents/

# 2. Load the schedule (runs daily at 9 AM)
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist

# 3. Test immediately
launchctl start com.user.job_scraper
```

### Alternative: Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM)
0 9 * * * /path/to/job_scraper/run_task.sh >> /path/to/job_scraper/cron.log 2>&1
```

The automated pipeline will:
1. Start Chrome in debug mode
2. Scrape Indeed jobs
3. Scrape LinkedIn jobs
4. **Run AI matching on new jobs**
5. Log all results to `task.log`

**See [SCHEDULING.md](SCHEDULING.md) for detailed scheduling setup, troubleshooting, and customization options.**

## ⚠️ Important Notes

### Browser Automation

- The scraper automatically launches Chrome with remote debugging enabled
- Chrome will open in a separate profile (`/tmp/chrome_selenium`)
- You may need to manually dismiss cookie consent banners on first run

### Rate Limiting

The scraper includes built-in delays to mimic human behavior:
- 4-8 seconds between job cards
- 15-30 seconds between pages
- 15-30 seconds between keywords

### Legal & Ethical Considerations

- **Respect robots.txt**: Always check the website's robots.txt file
- **Terms of Service**: Ensure your use case complies with the platform's ToS
- **Rate Limiting**: The built-in delays help prevent server overload
- **Personal Use**: This tool is intended for personal job search assistance

### Troubleshooting

**Chrome connection fails:**
```bash
# Manually start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium"
```

**MongoDB connection issues:**
- Verify your `MONGO_URI` in `.env`
- Check network connectivity to MongoDB Atlas
- Ensure your IP is whitelisted in MongoDB Atlas

**Playwright errors:**
```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

## 🔧 Development

### Add New Data Fields

Modify the job data dictionary in scrapers:

```python
job_data = {
    "title": title,
    "company": company,
    "location": location,
    # Add custom fields here
    "salary": salary,
    "remote": is_remote,
}
```

### Add New Selectors

Update `config.py` with new CSS selectors:

```python
INDEED_CONFIG = {
    "selectors": {
        "job_card": ".mainContentTable",
        "job_title": "h3.jobTitle",
        # Add new selectors
        "company_name": ".companyName",
    }
}
```

## 📝 License

This project is for educational and personal use only. Please review and comply with the terms of service of Indeed and LinkedIn before using.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Contact

For questions or issues, please open an issue in the repository.

---

**Disclaimer**: This tool is intended for personal job search assistance. Users are responsible for ensuring their use complies with applicable laws and website terms of service.
