#!/usr/bin/env python3
"""
LinkedIn Quick Scraper — 12-hour window
========================================
Navigates directly to a pre-built LinkedIn search URL that filters for jobs
posted within the last 12 hours (f_TPR=r43200).  Designed to be run at
~11 AM each morning, right before the daily application session, so you
always apply to the freshest listings.

Typical usage
-------------
  python3 src/linkedin_quick_scraper.py              # 3 pages, up to 30 jobs/page
  python3 src/linkedin_quick_scraper.py -p 2         # limit to 2 pages
  python3 src/linkedin_quick_scraper.py -p 3 -j 20   # 3 pages, 20 jobs each
"""
import sys
import os

# Allow direct execution from the project root
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import random

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from db_mongo import init_db, save_job, is_job_id_exists, increment_scraper_stat
from config import MAX_JOBS_PER_PAGE, DEFAULT_MAX_PAGES, LINKEDIN_QUICK_CONFIG
from scraper_utils import pause, connect_browser, is_title_excluded, detect_job_detail_language, safe_text

# Re-use the core scraping helpers from the standard LinkedIn scraper
# (scroll logic, job-card extraction, pagination) — no duplication needed.
from linkedin_scraper import (
    scrape_jobs,
    go_to_next_page,
)

SOURCE = LINKEDIN_QUICK_CONFIG["source"]
QUICK_URL = LINKEDIN_QUICK_CONFIG["url"]
TIME_WINDOW_HOURS = LINKEDIN_QUICK_CONFIG["time_window_hours"]


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_quick_args():
    """Parse CLI arguments for the quick scraper."""
    parser = argparse.ArgumentParser(
        description=(
            f"LinkedIn quick scraper — fetches jobs posted in the last "
            f"{TIME_WINDOW_HOURS} hours using a pre-built search URL."
        )
    )
    parser.add_argument(
        "-p", "--max-pages",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help=f"Maximum pages to scrape (default: {DEFAULT_MAX_PAGES})",
    )
    parser.add_argument(
        "-j", "--max-jobs",
        type=int,
        default=MAX_JOBS_PER_PAGE,
        help=f"Maximum jobs to process per page (default: {MAX_JOBS_PER_PAGE})",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Scraping orchestration
# ---------------------------------------------------------------------------

def scrape_quick(page, max_pages: int, max_jobs_per_page: int) -> list:
    """
    Navigate to the pre-built quick-search URL and scrape *max_pages* pages.

    Args:
        page: Playwright page object (connected to the user's Chrome session).
        max_pages: Number of result pages to process.
        max_jobs_per_page: Maximum job cards to click per page.

    Returns:
        List of job-data dicts that were saved to MongoDB.
    """
    print(
        f"\n========== LinkedIn Quick Scrape "
        f"(last {TIME_WINDOW_HOURS} h) =========="
    )
    print(f"URL: {QUICK_URL}")
    page.goto(QUICK_URL, wait_until="domcontentloaded")
    pause(4, 7, "Waiting for quick-search results to load")

    all_jobs: list = []
    for page_index in range(max_pages):
        print(f"\n--- Quick scrape: page {page_index + 1}/{max_pages} ---")
        jobs = scrape_jobs(page, max_jobs=max_jobs_per_page)
        all_jobs.extend(jobs)
        if page_index < max_pages - 1:
            if not go_to_next_page(page):
                break
            pause(15, 30, "Rest between pages")

    return all_jobs


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    args = parse_quick_args()
    max_pages = args.max_pages
    max_jobs = args.max_jobs

    print(f"[Quick Scraper] Max pages : {max_pages}")
    print(f"[Quick Scraper] Max jobs/page : {max_jobs}")
    print(f"[Quick Scraper] Time window  : last {TIME_WINDOW_HOURS} hours")

    init_db()

    with sync_playwright() as playwright:
        browser = connect_browser(playwright, "LinkedIn")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        print("Log in to LinkedIn in the debug Chrome window if you have not already.")

        all_jobs = scrape_quick(page, max_pages=max_pages, max_jobs_per_page=max_jobs)

        # Chrome is the user's real session — do NOT close it.

    print(f"\nDone. Saved {len(all_jobs)} new LinkedIn jobs (quick run).")


if __name__ == "__main__":
    main()
