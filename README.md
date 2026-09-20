# Job Scraper - AI-Powered Job Search Assistant

An intelligent Python-based web scraper that automatically collects job listings from Indeed and LinkedIn, uses AI to analyze and match jobs to your profile, and helps you track opportunities efficiently.

## ✨ Features

- **Multi-Platform Scraping**: Automated job collection from Indeed and LinkedIn
- **AI-Powered Matching**: Uses OpenAI/Claude to analyze jobs and score matches (0-10)
- **Smart Deduplication**: Automatically detects and skips duplicate postings
- **Human-Like Behavior**: Random delays and scrolling patterns to avoid detection
- **MongoDB Integration**: Flexible storage and querying of job data
- **Automated Scheduling**: Daily execution via LaunchD or Cron
- **Match Analysis**: Provides match reasons, missing requirements, and red flags

## 📋 Prerequisites

- Python 3.8+
- Google Chrome browser
- MongoDB (local or MongoDB Atlas)
- OpenAI API key (for AI matching)

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /path/to/job_scraper
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# MongoDB Configuration
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?appName=Cluster0
# Or use local: mongodb://localhost:27017/

# Optional: Database name (defaults to "job_scraper")
# DB_NAME=job_scraper

# AI Configuration (for job matching)
OPENAI_API_KEY=sk-proj-your_key_here
AI_MODEL=gpt-4o-mini
MATCH_THRESHOLD=7.0
```

Get your OpenAI API key from: https://platform.openai.com/api-keys

### 3. Set Up Your Profile

Edit `docs/user_profile.md` with your resume and preferences:

```markdown
## Personal Information
- Name: Your Name
- Current Role: Software Engineer
- Years of Experience: 3+ years
- Location: Berlin, Germany

## Technical Skills
- Frontend: React, Vue.js, TypeScript
- Backend: Node.js, Python
- Database: MongoDB, PostgreSQL

## Preferences
- Work Style: Remote or hybrid
- Company Size: Startups or scale-ups
```

Edit `docs/matching_criteria.md` with your job requirements:

```markdown
## Must-Have Requirements
1. Position involves React or modern frameworks
2. Remote-friendly or Berlin-based
3. English-speaking environment

## Strong Preferences
1. Hybrid work option
2. Modern tech stack
3. Learning opportunities

## Red Flags (Avoid)
- No remote work options
- Unpaid trial periods
- Unclear compensation
```

### 4. Test Run

```bash
# Test Indeed scraper (1 page only)
python3 src/indeed_scraper.py -k "frontend" -p 1

# Test AI matching (3 jobs only)
python3 src/ai_matcher.py -l 3

# View results
python3 src/view_jobs.py --source indeed
```

### 5. Set Up Automation

Schedule daily execution:

```bash
# Copy LaunchD configuration
cp com.user.job_scraper.plist ~/Library/LaunchAgents/

# Load the schedule (runs daily at 9 AM)
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist

# Test immediately
launchctl start com.user.job_scraper
```

## 📁 Project Structure

```
job_scraper/
├── src/                        # Python source files
│   ├── ai_matcher.py          # AI-powered job matching engine
│   ├── config.py              # Central configuration
│   ├── db_mongo.py            # MongoDB operations
│   ├── indeed_scraper.py      # Indeed scraper
│   ├── linkedin_scraper.py    # LinkedIn scraper
│   ├── scraper_utils.py       # Shared utility functions
│   └── view_jobs.py           # View and query jobs
├── docs/                       # Configuration & profile files
│   ├── user_profile.md        # Your resume/profile (required for AI)
│   └── matching_criteria.md   # Job matching criteria (required for AI)
├── run_task.sh                # Automated execution script
├── com.user.job_scraper.plist # macOS LaunchD configuration
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## 🎯 Usage

### Scrape Job Listings

#### Indeed Scraper

```bash
# Use default keywords and pages
python3 src/indeed_scraper.py

# Specify custom keywords
python3 src/indeed_scraper.py --keywords "python developer" "data scientist"

# Limit pages per keyword
python3 src/indeed_scraper.py --max-pages 2

# Combined options
python3 src/indeed_scraper.py -k "frontend" -p 1
```

#### LinkedIn Scraper

```bash
# Use default keywords
python3 src/linkedin_scraper.py

# Specify custom keywords
python3 src/linkedin_scraper.py --keywords "backend" "devops"

# Limit pages per keyword
python3 src/linkedin_scraper.py --max-pages 2
```

### AI Job Matching

After scraping, use AI to find the best matches:

```bash
# Analyze all new jobs
python3 src/ai_matcher.py

# Test with limited jobs first
python3 src/ai_matcher.py --limit 5

# Only process Indeed jobs
python3 src/ai_matcher.py --source indeed

# Set custom match threshold (0-10)
python3 src/ai_matcher.py --threshold 8.0

# Combined options
python3 src/ai_matcher.py -s linkedin -t 7.5 -l 20
```

The AI will:
- Analyze each job against your profile
- Score each job from 0-10
- Save high-quality matches (≥7.0) to `matched_jobs` collection
- Provide detailed reasons for each match/rejection

### Complete Pipeline

Run everything at once:

```bash
./run_task.sh
```

This will:
1. Start Chrome in debug mode
2. Scrape Indeed jobs
3. Scrape LinkedIn jobs
4. Run AI matching on new jobs
5. Log all results to `task.log`

### Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--keywords` | `-k` | Search keywords (space-separated) | `DEFAULT_KEYWORDS` |
| `--max-pages` | `-p` | Pages to scrape per keyword | `3` |
| `--limit` | `-l` | Limit number of jobs to process | All |
| `--source` | `-s` | Filter by source (indeed/linkedin) | All |
| `--threshold` | `-t` | Minimum match score to save | `7.0` |

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

### Collection: `matched_jobs`

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

```python
from src.db_mongo import init_db, get_jobs_by_source, get_collection

# Initialize database connection
init_db()

# Get all Indeed jobs
indeed_jobs = get_jobs_by_source("indeed")

# Get matched jobs sorted by score
matched = get_collection("matched_jobs")
best_matches = matched.find().sort("match_score", -1).limit(10)

# View matches
for job in best_matches:
    print(f"{job['match_score']}/10 - {job['title']} at {job['company']}")
    print(f"  Link: {job['link']}")
    print(f"  Reasons: {', '.join(job['match_reasons'])}\n")
```

## 🤖 Automated Scheduling

### LaunchD Setup (macOS - Recommended)

LaunchD is the native macOS scheduling system and is more reliable than cron.

```bash
# 1. Copy the plist file
cp com.user.job_scraper.plist ~/Library/LaunchAgents/

# 2. Load the schedule (runs daily at 9 AM)
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist

# 3. Test immediately
launchctl start com.user.job_scraper

# 4. Verify it's loaded
launchctl list | grep job_scraper
```

#### Customize Schedule

Edit `com.user.job_scraper.plist` to change the time:

```xml
<!-- Run every day at 9:00 AM -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

For multiple times per day:

```xml
<key>StartCalendarInterval</key>
<array>
    <dict>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</array>
```

Then reload:

```bash
launchctl unload ~/Library/LaunchAgents/com.user.job_scraper.plist
launchctl load ~/Library/LaunchAgents/com.user.job_scraper.plist
```

#### Management Commands

```bash
# Start the job immediately
launchctl start com.user.job_scraper

# Stop the scheduled job
launchctl stop com.user.job_scraper

# Unload (disable) the job
launchctl unload ~/Library/LaunchAgents/com.user.job_scraper.plist
```

#### Check Logs

```bash
# View standard output
tail -f stdout.log

# View errors
tail -f stderr.log

# View task log
tail -f task.log
```

### Cron Setup (Alternative)

Cron is the traditional Unix scheduler.

1. **Give cron Full Disk Access** (macOS Catalina+)
   - System Preferences → Security & Privacy → Privacy
   - Select "Full Disk Access"
   - Add `/usr/sbin/cron`

2. **Edit crontab**
   
   ```bash
   crontab -e
   ```

3. **Add the schedule** (runs daily at 9 AM)
   
   ```cron
   0 9 * * * /path/to/job_scraper/run_task.sh >> /path/to/job_scraper/cron.log 2>&1
   ```

#### Cron Examples

```cron
# Every day at 9 AM
0 9 * * * /path/to/run_task.sh

# Every day at 9 AM and 6 PM
0 9,18 * * * /path/to/run_task.sh

# Every weekday (Mon-Fri) at 9 AM
0 9 * * 1-5 /path/to/run_task.sh

# Every 6 hours
0 */6 * * * /path/to/run_task.sh
```

## 🎓 AI Matching Guide

### Understanding Match Scores

- **9-10**: Excellent match - Apply immediately
- **7-8**: Good match - Strongly consider
- **4-6**: Moderate match - Review carefully
- **0-3**: Poor match - Not saved by default

### Cost Estimation

**OpenAI Pricing (as of 2024):**

- **GPT-4o-mini** (recommended):
  - ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
  - Typical cost: $0.001-0.003 per job
  - **100 jobs ≈ $0.10-0.30**

- **GPT-4o**:
  - ~$2.50 per 1M input tokens, ~$10.00 per 1M output tokens
  - Typical cost: $0.02-0.05 per job
  - **100 jobs ≈ $2-5**

💡 **Tip**: Start with `gpt-4o-mini` for testing, then upgrade if needed.

### Customization

#### Adjust Match Threshold

In `.env`:
```bash
# Only save excellent matches
MATCH_THRESHOLD=8.5

# Save more matches for review
MATCH_THRESHOLD=6.0
```

#### Modify AI Prompt

Edit `src/ai_matcher.py` → `build_matching_prompt()` to customize:
- Scoring criteria
- Analysis format
- Specific requirements to check

#### Use Different AI Provider

For Claude (Anthropic):

1. Install SDK:
   ```bash
   pip install anthropic
   ```

2. Update `.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-xxxxx
   AI_MODEL=claude-3-5-sonnet-20241022
   ```

3. Modify `src/ai_matcher.py` to use Anthropic client

### Best Practices

1. **Test with small batches first**
   ```bash
   python3 src/ai_matcher.py --limit 3
   ```

2. **Review AI recommendations**
   - Don't blindly trust scores
   - Read the match_reasons and red_flags
   - Adjust criteria if results are off

3. **Refine your profile**
   - Update `docs/user_profile.md` with specific skills
   - Be clear about must-haves in `docs/matching_criteria.md`
   - Add examples of ideal job descriptions

4. **Monitor costs**
   - Check OpenAI usage dashboard
   - Start with `gpt-4o-mini`
   - Set budgets in OpenAI account settings

5. **Iterate on criteria**
   - If too many false positives, increase threshold
   - If missing good jobs, lower threshold or refine criteria
   - Adjust prompt for better results

### Workflow Integration

After matching, update job status:

```python
from src.db_mongo import get_collection
from datetime import datetime

matched = get_collection("matched_jobs")
matched.update_one(
    {"job_id": "123456", "source": "linkedin"},
    {
        "$set": {
            "status": "applied",
            "applied_at": datetime.utcnow(),
            "notes": "Applied via LinkedIn, mentioned referral"
        }
    }
)
```

## ⚙️ Configuration

### Search Keywords

Edit `src/config.py`:

```python
DEFAULT_KEYWORDS = [
    "frontend developer",
    "react developer",
    "full stack engineer",
    "software engineer",
]
```

### Scraping Limits

```python
DEFAULT_MAX_PAGES = 3        # Pages per keyword
MAX_JOBS_PER_PAGE = 30       # Jobs to process per page
CDP_PORT = 9222              # Chrome DevTools Protocol port
```

### Indeed Configuration

```python
INDEED_CONFIG = {
    "base_url": "https://de.indeed.com/jobs",
    "fromage": "1",          # Posted within last 1 day
    "results_per_page": 10,
    "selectors": {
        "job_card": ".mainContentTable",
        "job_title": "h3.jobTitle",
        "company_name": ".companyName",
        # ... more selectors
    }
}
```

### LinkedIn Configuration

```python
LINKEDIN_CONFIG = {
    "base_url": "https://www.linkedin.com/jobs/search/",
    "geo_id": "101282230",   # Germany
    "time_filter": "r86400", # Last 24 hours
    "selectors": {
        "job_card": ".job-search-card",
        "job_title": ".base-search-card__title",
        # ... more selectors
    }
}
```

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

## 🐛 Troubleshooting

### Chrome connection fails

```bash
# Manually start Chrome with debugging
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="/tmp/chrome_selenium"
```

### MongoDB connection issues

- Verify your `MONGO_URI` in `.env`
- Check network connectivity to MongoDB Atlas
- Ensure your IP is whitelisted in MongoDB Atlas

### Playwright errors

```bash
# Reinstall Playwright browsers
playwright install --force chromium
```

### AI API key errors

```
Error: AI API key not configured
```

- Check `.env` file exists
- Verify `OPENAI_API_KEY` is set
- Make sure there are no extra spaces or quotes
- Verify the API key is valid at https://platform.openai.com/api-keys

### No new jobs to process

```
No new jobs to process.
```

- All jobs may have been processed already
- Run scrapers first: `python3 src/indeed_scraper.py`
- Check database: all jobs with status="new" will be processed

### LaunchD not working

```bash
# Check if loaded
launchctl list | grep job_scraper

# View detailed status
launchctl print gui/$(id -u)/com.user.job_scraper

# Check system logs
log show --predicate 'process == "launchd"' --last 1h | grep job_scraper
```

### High API costs

- Use `gpt-4o-mini` instead of `gpt-4o`
- Set higher threshold to analyze fewer jobs
- Use `--limit` to control batch size
- Reduce job description length in prompt

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

Update `src/config.py` with new CSS selectors:

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

### Add Notifications (Optional)

#### macOS Notification

Install `terminal-notifier`:

```bash
brew install terminal-notifier
```

Add to the end of `run_task.sh`:

```bash
terminal-notifier -title "Job Scraper" \
  -message "Daily job scraping completed" \
  -sound default
```

#### Email Notification

Configure mail and add to `run_task.sh`:

```bash
echo "Job scraper completed at $(date)" | \
  mail -s "Job Scraper Report" your_email@example.com
```

## 📝 License

This project is for educational and personal use only. Please review and comply with the terms of service of Indeed and LinkedIn before using.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For questions or issues, please open an issue in the repository.

---

**Disclaimer**: This tool is intended for personal job search assistance. Users are responsible for ensuring their use complies with applicable laws and website terms of service.

**Note**: All comments in the codebase are in English for better collaboration and maintenance.
