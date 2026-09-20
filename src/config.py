"""
Job Scraper Configuration
Centralized configuration for all scrapers
"""

# ===== Common Configuration =====

# Default search keywords
DEFAULT_KEYWORDS = [
    "frontend",
    "full stack",
    "full-stack",
    "fullstack",
    "ai engineer",
    "product engineer",
    "software engineer",
]

# Scraping parameters
DEFAULT_MAX_PAGES = 3  # Maximum pages to scrape per keyword
MAX_JOBS_PER_PAGE = 30  # Maximum jobs to process per page

# Chrome debugging configuration
CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA_DIR = "/tmp/chrome_selenium"


# ===== Indeed Platform Configuration =====
INDEED_CONFIG = {
    "source": "indeed",
    "base_url": "https://de.indeed.com/jobs",
    "fromage": "1",  # Posted within: last 1 day
    "results_per_page": 10,  # Indeed SERP: 10 results per page
    
    # Selectors
    "selectors": {
        "job_card": ".mainContentTable",
        "job_title": "h3.jobTitle",
        "detail": '[data-testid="viewjob-main-content"]',
    }
}


# ===== LinkedIn Platform Configuration =====
LINKEDIN_CONFIG = {
    "source": "linkedin",
    "base_url": "https://www.linkedin.com/jobs/search/",
    "geo_id": "101282230",  # Germany
    "time_filter": "r86400",  # Last 24 hours
    
    # Selectors
    "selectors": {
        "job_card": ".scaffold-layout__list-item",
        "job_link": "a.job-card-container__link",
    }
}
