#!/usr/bin/env python3
"""
LinkedIn Job Scraper
Scrapes job listings from LinkedIn and saves them to MongoDB
"""
import sys
import os
from urllib.parse import quote_plus
import random
import re

# Add src/ to path so package imports work when run as a script
_SRC_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SRC_ROOT not in sys.path:
    sys.path.insert(0, _SRC_ROOT)

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from core.db_mongo import init_db, save_job, is_job_id_exists, increment_scraper_stat
from core.config import (
    MAX_JOBS_PER_PAGE,
    LINKEDIN_CONFIG,
)
from core.scraper_utils import (
    pause,
    safe_text,
    parse_args,
    connect_browser,
    open_scraper_page,
    goto_page,
    is_title_excluded,
    detect_job_detail_language,
)

# LinkedIn configuration
BASE_URL = LINKEDIN_CONFIG["base_url"]
GEO_ID = LINKEDIN_CONFIG["geo_id"]
TIME_FILTER = LINKEDIN_CONFIG["time_filter"]
SOURCE = LINKEDIN_CONFIG["source"]

# LinkedIn selectors
JOB_CARD_SELECTOR = LINKEDIN_CONFIG["selectors"]["job_card"]
JOB_LINK_SELECTOR = LINKEDIN_CONFIG["selectors"]["job_link"]


def extract_job_id_from_url(url):
    """
    Extract the LinkedIn job ID from a job URL.
    Tries multiple URL patterns to find the job ID.
    
    Args:
        url: LinkedIn job URL
        
    Returns:
        Job ID string or None if not found
    """
    if not url:
        return None
    match = re.search(r"/jobs/view/(\d+)", url)
    if match:
        return match.group(1)
    match = re.search(r"[?&]currentJobId=(\d+)", url)
    if match:
        return match.group(1)
    return None



def jobs_search_url(keyword):
    """
    Build LinkedIn search URL for a given keyword.
    
    Args:
        keyword: Search keyword
        
    Returns:
        Full search URL with geo and time filters
    """
    encoded = quote_plus(keyword)
    return (
        f"{BASE_URL}"
        f"?keywords={encoded}&f_TPR={TIME_FILTER}&geoId={GEO_ID}"
        "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"
    )


def get_status(job):
    """
    Extract job application status from LinkedIn job card.
    
    Args:
        job: Playwright locator for a job card element
        
    Returns:
        Status text or "new" as default
    """
    text = safe_text(job.locator(".job-card-container__footer-job-state"))
    return text or "new"


def scroll_job_list(page):
    """
    Scroll the LinkedIn job list to load more cards.
    LinkedIn uses virtual scrolling, so this forces more cards to render.
    
    Args:
        page: Playwright page object
    """
    print("Scrolling the job list to load more cards...")
    list_container = page.locator(".scaffold-layout__list").first
    last_count = 0
    for i in range(5):
        cards = page.locator(JOB_CARD_SELECTOR)
        count = cards.count()
        if count > 0:
            cards.last.scroll_into_view_if_needed()
        elif list_container.count() > 0:
            list_container.evaluate("el => { el.scrollTop = el.scrollHeight }")
        else:
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pause(1.5, 2.5)
        new_count = page.locator(JOB_CARD_SELECTOR).count()
        print(f"Scroll {i + 1}: {last_count} -> {new_count} cards")
        if new_count <= last_count:
            print("Card count did not increase, stop scrolling")
            break
        last_count = new_count
    pause(2, 4, "Waiting for the list to finish rendering")


def scrape_jobs(page, max_jobs=MAX_JOBS_PER_PAGE):
    """
    Scrape job listings from the current LinkedIn search results page.
    
    Args:
        page: Playwright page object
        max_jobs: Maximum number of jobs to process per page
        
    Returns:
        List of job data dictionaries that were successfully saved
    """
    scroll_job_list(page)
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

            job = cards.nth(index)
            job.scroll_into_view_if_needed()
            job.locator(JOB_LINK_SELECTOR).first.wait_for(state="visible", timeout=10000)

            link = job.locator(JOB_LINK_SELECTOR).first
            title = (link.get_attribute("aria-label") or link.inner_text() or "").strip()
            href_value = link.get_attribute("href") or ""
            company = safe_text(job.locator(".artdeco-entity-lockup__subtitle span"))
            location = safe_text(job.locator(".job-card-container__metadata-wrapper li span"))
            status = get_status(job)

            print(f"Job {index + 1}: {title} | {company} | {location}")

            job_id = extract_job_id_from_url(href_value)
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
            job.click()
            page.wait_for_selector(
                ".job-details-jobs-unified-top-card__tertiary-description-container, .jobs-box__html-content",
                timeout=15000,
            )
            pause(1.0, 2.0)

            apply_number = safe_text(
                page.locator(".job-details-jobs-unified-top-card__tertiary-description-container")
            )

            desc_locator = page.locator(".jobs-box__html-content")
            job_desc_text = safe_text(desc_locator, timeout=5000)
            lang, german_share = detect_job_detail_language(job_desc_text)
            print(
                f"Job {index + 1}: description length {len(job_desc_text)}, "
                f"language={lang or 'unknown'}, german_share={german_share:.0%}"
            )

            if lang == "de":
                increment_scraper_stat("german_filtered")
                print(f"Job {index + 1}: German description detected, skip save")
            else:
                job_data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "status": status,
                    "link": href_value,
                    "job_id": job_id,
                    "applicants": apply_number,
                    "description": job_desc_text,
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


def go_to_next_page(page):
    """
    Navigate to the next page of LinkedIn search results.
    
    Args:
        page: Playwright page object
        
    Returns:
        True if successfully navigated to next page, False otherwise
    """
    next_btn = page.locator('button[aria-label="View next page"]')
    if next_btn.count() == 0 or not next_btn.first.is_enabled():
        print("No next-page button, stop paging")
        return False
    next_btn.first.scroll_into_view_if_needed()
    pause(0.4, 0.8)
    next_btn.first.click()
    pause(5, 10, "Waiting after pagination")
    return True


def scrape_keyword(page, keyword, max_pages, max_jobs_per_page=MAX_JOBS_PER_PAGE):
    """
    Scrape multiple pages of LinkedIn results for a single keyword.
    
    Args:
        page: Playwright page object
        keyword: Search keyword
        max_pages: Maximum number of pages to scrape
        max_jobs_per_page: Maximum jobs to process per page
        
    Returns:
        List of all job data dictionaries saved for this keyword
    """
    print(f"\n========== Keyword: {keyword} ==========")
    goto_page(page, jobs_search_url(keyword))
    pause(4, 7, f"Waiting for search results: {keyword}")

    all_jobs = []
    for page_index in range(max_pages):
        print(f"\n--- {keyword}: page {page_index + 1}/{max_pages} ---")
        jobs = scrape_jobs(page, max_jobs=max_jobs_per_page)
        all_jobs.extend(jobs)
        if page_index < max_pages - 1:
            if not go_to_next_page(page):
                break
            pause(15, 30, "Rest between pages")
    return all_jobs


def main():
    args = parse_args()
    keywords = args.keywords
    max_pages = args.max_pages
    print(f"Keywords: {keywords}")
    print(f"Max pages per keyword: {max_pages}")

    init_db()
    all_jobs = []

    with sync_playwright() as playwright:
        browser = connect_browser(playwright, "LinkedIn")
        context = browser.contexts[0]
        page = open_scraper_page(context, bring_to_front=True)
        print("Log in to LinkedIn in the debug Chrome window if you have not already.")

        for i, keyword in enumerate(keywords):
            jobs = scrape_keyword(page, keyword, max_pages)
            all_jobs.extend(jobs)
            if i < len(keywords) - 1:
                pause(15, 30, "Rest between keywords")

        # Do not close the connected Chrome; it is the user's real session.

    print(f"\nDone. Saved {len(all_jobs)} new LinkedIn jobs this run.")


if __name__ == "__main__":
    main()
