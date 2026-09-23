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
DEFAULT_MAX_PAGES = 2  # Maximum pages to scrape per keyword
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


# ===== LinkedIn Quick Search Configuration (12-hour window) =====
# Used by the morning quick-scrape run (11 AM) to capture jobs posted
# in the last 12 hours — complements the full 24-hour evening scrape.
LINKEDIN_QUICK_CONFIG = {
    "source": "linkedin",
    # Direct search URL — keywords encode an OR query across all target roles.
    # f_TPR=r43200 → posted within the last 43 200 seconds (12 hours).
    "url": (
        "https://www.linkedin.com/jobs/search-results/"
        "?keywords=full-time%20Full%20Stack%20Engineer%20or%20Frontend%20Developer"
        "%20or%20Product%20Engineer%20or%20Generative%20AI%20Engineer"
        "%2C%20on-site%20or%20hybrid%20or%20remote"
        "&geoId=101282230"
        "&f_TPR=r43200"
        "&origin=JOB_SEARCH_PAGE_JOB_FILTER"
        "&refresh=true"
    ),
    "time_window_hours": 12,

    # Selectors (same as standard LinkedIn)
    "selectors": {
        "job_card": ".scaffold-layout__list-item",
        "job_link": "a.job-card-container__link",
    }
}
