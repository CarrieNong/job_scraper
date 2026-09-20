# Job Scraper

A Python-based web scraper that automatically collects job listings from Indeed and LinkedIn, stores them in MongoDB, and helps you track job opportunities efficiently.

## 🚀 Features

- **Multi-Platform Support**: Scrapes job listings from both Indeed and LinkedIn
- **Smart Deduplication**: Automatically detects and skips duplicate job postings using job IDs
- **Human-Like Behavior**: Implements random delays and scrolling patterns to avoid detection
- **MongoDB Integration**: Stores all job data in MongoDB with flexible querying capabilities
- **Customizable Search**: Configure keywords, location, and time filters
- **Browser Automation**: Uses Playwright with Chrome DevTools Protocol for reliable scraping
- **Automated Scheduling**: Includes shell script for scheduled task execution

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

### Run Indeed Scraper

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

### Run LinkedIn Scraper

```bash
# Use default keywords and pages
python3 linkedin_scraper.py

# Specify custom keywords
python3 linkedin_scraper.py --keywords "backend" "devops"

# Limit pages per keyword
python3 linkedin_scraper.py --max-pages 2
```

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
├── config.py              # Central configuration for all scrapers
├── scraper_utils.py       # Shared utility functions
├── db_mongo.py            # MongoDB database operations
├── indeed_scraper.py      # Indeed job scraper
├── linkedin_scraper.py    # LinkedIn job scraper
├── run_task.sh            # Shell script for automated execution
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
└── .gitignore            # Git ignore rules
```

## 🗄 Database Schema

Jobs are stored in MongoDB with the following structure:

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

### Query Jobs

Use the MongoDB client or `db_mongo.py` functions:

```python
from db_mongo import init_db, get_jobs_by_source, count_jobs

# Initialize database connection
init_db()

# Get all Indeed jobs
indeed_jobs = get_jobs_by_source("indeed")

# Count jobs by source
count = count_jobs("linkedin")
```

## 🤖 Automated Scheduling

Use `run_task.sh` for scheduled execution (e.g., with cron):

```bash
# Make script executable
chmod +x run_task.sh

# Edit crontab
crontab -e

# Add daily job at 9 AM
0 9 * * * /path/to/job_scraper/run_task.sh
```

The script will:
1. Start Chrome in debug mode
2. Run the scrapers
3. Log execution times to `task.log`

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
