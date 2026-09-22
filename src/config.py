"""
Job Scraper Configuration
Centralized configuration for all scrapers
"""

# ===== Common Configuration =====

# Default search keywords
DEFAULT_KEYWORDS = [
    "frontend",
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


# ===== Title Pre-filter (skip clicking if title matches any pattern) =====
# Patterns are case-insensitive regex. Use \b for word boundaries where needed.
# Java uses \b to avoid matching JavaScript.
TITLE_EXCLUDE_KEYWORDS = [
    r"\bJava\b",           # Java (not JavaScript)
    r"\bCloud\b",
    r"\bLead\b",
    r"\bStaff\b",
    r"\bFounding\b",
    r"\bDevOps\b",
    r"C#",                 # C# / C++/C#
    r"\.NET",              # .NET
    r"\bEmbedded\b",
    r"C\+\+",              # C++
    r"\bQA\b",             # QA Engineer
    r"\bTest\s+Engineer\b",
    r"\bProject\s+Manager\b",
    r"\bFlutter\b",
    r"\bReact\s+Native\b",
    r"\bPrincipal\b",
    r"\bManager\b",        # also catches Project Manager
    r"\bAndroid\b",
    r"\bArchitect\b",
    r"\bData\s+Scientist\b",
    r"\bData\s+Engineer\b",
    r"\bData\s+Analyst\b",
    r"\bQuality\s+Engineer\b",
    r"\bDesign\s+Engineer\b",
    r"\biOS\b",
    r"\bSwift\b",
    r"\bForward\s+Deployed\s+Engineer\b",
    r"\bInfrastructure\s+Engineer\b",
    r"\bAnalytics\s+Engineer\b",
    r"\bKubernetes\b",
    r"\bLinux\b",
    r"\bApplied\s+Researcher\b",
    r"\bMachine\s+Learning\b",
    r"\bPHP\b",
    r"\bRobot\s+Learning\s+Engineer\b",
    r"\bCAD\s+Engineer\b",
    r"\bElectronic\s+Design\b",
    r"\bResearcher\b",
    r"\bTechnical\s+Customer\s+Support\b",
    r"\bHead\s+of\b",
    r"\bSecurity\s+Engineer\b",
    r"\bRobotics\s+Engineer\b",
    r"\bSystems\s+Engineer\b",
    r"\bProcess\s+Validation\s+Engineer\b",
    r"\bSafety\s+Engineer\b",
]


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
