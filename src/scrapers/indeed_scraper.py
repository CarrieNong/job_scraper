#!/usr/bin/env python3
"""
Indeed Job Scraper
Scrapes job listings from Indeed and saves them to MongoDB
"""
import sys
import os
from urllib.parse import quote_plus
import random

# Add src/ to path so package imports work when run as a script
_SRC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.db_mongo import init_db, save_job, is_job_id_exists, increment_scraper_stat
from core.config import (
    MAX_JOBS_PER_PAGE,
    INDEED_CONFIG,
)
from core.scraper_utils import (
    pause,
    safe_text,
    safe_attr,
    parse_args,
    connect_browser,
    open_scraper_page,
    is_title_excluded,
    detect_job_detail_language,
    strip_html,
)

# Indeed configuration
BASE_URL = INDEED_CONFIG["base_url"]
FROMAGE = INDEED_CONFIG["fromage"]
SOURCE = INDEED_CONFIG["source"]
RESULTS_PER_PAGE = INDEED_CONFIG["results_per_page"]

# Indeed selectors
JOB_CARD_SELECTOR = INDEED_CONFIG["selectors"]["job_card"]
JOB_TITLE_SELECTOR = INDEED_CONFIG["selectors"]["job_title"]
DETAIL_SELECTOR = INDEED_CONFIG["selectors"]["detail"]



def jobs_search_url(keyword, start=0):
    """
    Build Indeed search URL for a given keyword and pagination offset.
    
    Args:
        keyword: Search keyword
        start: Job offset for pagination
        
    Returns:
        Full search URL
    """
    encoded = quote_plus(keyword)
    url = f"{BASE_URL}?q={encoded}&l=&fromage={FROMAGE}&from=searchOnDesktopSerp"
    if start > 0:
        url += f"&start={start}"
    return url


def dismiss_overlays(page):
    """Best-effort dismiss cookie / consent dialogs on Indeed DE."""
    candidates = [
        'button#onetrust-accept-btn-handler',
        'button:has-text("Alle akzeptieren")',
        'button:has-text("Accept All")',
        'button:has-text("Accept cookies")',
        'button:has-text("Ich stimme zu")',
    ]
    for selector in candidates:
        try:
            btn = page.locator(selector)
            if btn.count() > 0 and btn.first.is_visible():
                btn.first.click(timeout=2000)
                pause(0.5, 1.0)
                return
        except Exception:
            continue


def extract_card_fields(card):
    """
    Extract title, job_id, and URL from an Indeed job card.
    
    Title resolution order:
      1. `title` attribute on the <span> inside h3.jobTitle  (most reliable)
      2. Inner text of that <span>
      3. Inner text of the whole h3.jobTitle heading

    Args:
        card: Playwright locator for a job card element
        
    Returns:
        Tuple of (title, job_id, href)
    """
    title_heading = card.locator(JOB_TITLE_SELECTOR).first
    span = title_heading.locator("span").first
    # Prefer the span's title attribute (Indeed DE sets it reliably)
    title = safe_attr(span, "title") or safe_text(span)
    if not title:
        title = safe_text(title_heading)

    link = title_heading.locator("a").first
    job_id = safe_attr(link, "id")
    href = safe_attr(link, "href")
    if href and href.startswith("/"):
        href = f"https://de.indeed.com{href}"
    elif not href and job_id:
        # Fallback: Indeed job keys are often usable as jk=
        jk = job_id.replace("job_", "").replace("sj_", "")
        href = f"https://de.indeed.com/viewjob?jk={jk}"

    return title, job_id, href


def scrape_jobs(page, max_jobs=MAX_JOBS_PER_PAGE):
    """
    Scrape job listings from the current Indeed search results page.
    
    Args:
        page: Playwright page object
        max_jobs: Maximum number of jobs to process per page
        
    Returns:
        List of job data dictionaries that were successfully saved
    """
    page.wait_for_selector(JOB_CARD_SELECTOR, timeout=15000)
    total_cards = page.locator(JOB_CARD_SELECTOR).count()
    limit = min(max_jobs, total_cards)
    jobs_data = []
    print(f"Found {total_cards} job cards, processing the first {limit}")

    for index in range(limit):
        print(f"\n=== Job {index + 1}/{limit} ===")
        try:
            cards = page.locator(JOB_CARD_SELECTOR)
            if index >= cards.count():
                print(f"Job {index + 1}: index out of range, skip")
                continue

            card = cards.nth(index)
            card.scroll_into_view_if_needed()
            title, job_id, href_value = extract_card_fields(card)
            print(f"Job {index + 1}: {title} | id={job_id}")

            if not job_id:
                print(f"Job {index + 1}: could not extract job_id, skip")
                continue

            if is_title_excluded(title):
                print(f"Job {index + 1}: title excluded by filter, skip → {title}")
                continue

            if is_job_id_exists(job_id, SOURCE):
                print(f"Job {index + 1}: job_id {job_id} already in DB, skip click")
                continue

            # Title passed + new job → count as a candidate we evaluated
            increment_scraper_stat("title_passed_clicked")
            card.click()
            page.wait_for_selector(DETAIL_SELECTOR, timeout=15000)
            pause(1.0, 2.0)

            detail = page.locator(DETAIL_SELECTOR).first
            description = strip_html(detail.inner_html(timeout=10000) or "")
            lang, german_share = detect_job_detail_language(description)
            print(
                f"Job {index + 1}: description length {len(description)}, "
                f"language={lang or 'unknown'}, german_share={german_share:.0%}"
            )

            if lang == "de":
                increment_scraper_stat("german_filtered")
                print(f"Job {index + 1}: German description detected, skip save")
            else:
                # company / location / applicants are left empty for now.
                job_data = {
                    "title": title,
                    "company": "",
                    "location": "",
                    "status": "new",
                    "link": href_value,
                    "job_id": job_id,
                    "applicants": "",
                    "description": description,
                    "source": SOURCE,
                }

                if save_job(job_data):
                    jobs_data.append(job_data)
                    print(f"Job {index + 1}: saved job_id {job_id}")

            if random.random() < 0.3:
                pause(1, 3, f"Job {index + 1}: extra think time")
            pause(4, 8, f"Job {index + 1}: wait before the next card")

        except PlaywrightTimeoutError:
            print(f"Job {index + 1}: timed out while loading details")
        except Exception as e:
            print(f"Job {index + 1}: error {type(e).__name__}: {e}")
            continue

    print(f"\n=== Page done, saved {len(jobs_data)} new jobs ===")
    return jobs_data


def scrape_keyword(page, keyword, max_pages, max_jobs_per_page=MAX_JOBS_PER_PAGE):
    """
    Scrape multiple pages of Indeed results for a single keyword.
    
    Args:
        page: Playwright page object
        keyword: Search keyword
        max_pages: Maximum number of pages to scrape
        max_jobs_per_page: Maximum jobs to process per page
        
    Returns:
        List of all job data dictionaries saved for this keyword
    """
    print(f"\n========== Keyword: {keyword} ==========")
    all_jobs = []

    for page_index in range(max_pages):
        start = page_index * RESULTS_PER_PAGE
        print(f"\n--- {keyword}: page {page_index + 1}/{max_pages} (start={start}) ---")
        page.goto(jobs_search_url(keyword, start=start), wait_until="domcontentloaded")
        pause(4, 7, f"Waiting for search results: {keyword}")
        dismiss_overlays(page)

        try:
            page.wait_for_selector(JOB_CARD_SELECTOR, timeout=15000)
        except PlaywrightTimeoutError:
            print(f"No job cards for {keyword} on page {page_index + 1}, stop paging")
            break

        jobs = scrape_jobs(page, max_jobs=max_jobs_per_page)
        all_jobs.extend(jobs)

        if page_index < max_pages - 1:
            pause(15, 30, "Rest between pages")

    return all_jobs


def main():
    args = parse_args()
    keywords = args.keywords
    max_pages = args.max_pages
    print(f"Source: {SOURCE}")
    print(f"Keywords: {keywords}")
    print(f"Max pages per keyword: {max_pages}")

    init_db()
    all_jobs = []

    with sync_playwright() as playwright:
        browser = connect_browser(playwright, "Indeed")
        context = browser.contexts[0]
        page = open_scraper_page(context)
        print("Use the debug Chrome window. Dismiss Indeed cookie banners if prompted.")

        for i, keyword in enumerate(keywords):
            jobs = scrape_keyword(page, keyword, max_pages)
            all_jobs.extend(jobs)
            if i < len(keywords) - 1:
                pause(15, 30, "Rest between keywords")

    print(f"\nDone. Saved {len(all_jobs)} new Indeed jobs this run.")


if __name__ == "__main__":
    main()
