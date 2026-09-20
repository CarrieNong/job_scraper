from urllib.parse import quote_plus
import argparse
import random
import re
import socket
import subprocess
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from db_mongo import init_db, save_job, is_job_id_exists

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA_DIR = "/tmp/chrome_selenium"

# Search filters: Germany + posted in the last 24 hours
GEO_ID = "101282230"
TIME_FILTER = "r86400"
DEFAULT_KEYWORDS = ["frontend", "full stack","full-stack","fullstack", "ai engineer", "product engineer", "software engineer"]
DEFAULT_MAX_PAGES = 3
MAX_JOBS_PER_PAGE = 30
SOURCE = "linkedin"
JOB_CARD_SELECTOR = ".scaffold-layout__list-item"
JOB_LINK_SELECTOR = "a.job-card-container__link"


def pause(min_seconds, max_seconds, message=None):
    """Sleep a random interval to look less like a bot."""
    delay = random.uniform(min_seconds, max_seconds)
    if message:
        print(f"{message} ({delay:.1f}s)")
    time.sleep(delay)


def extract_job_id_from_url(url):
    """Extract the LinkedIn job id from a job URL."""
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
    encoded = quote_plus(keyword)
    return (
        "https://www.linkedin.com/jobs/search/"
        f"?keywords={encoded}&f_TPR={TIME_FILTER}&geoId={GEO_ID}"
        "&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"
    )


def safe_text(locator, timeout=3000):
    try:
        if locator.count() == 0:
            return ""
        return (locator.first.inner_text(timeout=timeout) or "").strip()
    except Exception:
        return ""


def get_status(job):
    text = safe_text(job.locator(".job-card-container__footer-job-state"))
    return text or "new"


def scroll_job_list(page):
    """Scroll the job list so LinkedIn's virtual list renders more cards."""
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


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape LinkedIn jobs into SQLite.")
    parser.add_argument(
        "--keywords",
        "-k",
        nargs="+",
        default=DEFAULT_KEYWORDS,
        help='Search keywords. Example: -k frontend "full stack" "ai engineer"',
    )
    parser.add_argument(
        "--max-pages",
        "-p",
        type=int,
        default=DEFAULT_MAX_PAGES,
        help="How many result pages to scrape per keyword.",
    )
    return parser.parse_args()


def scrape_jobs(page, max_jobs=MAX_JOBS_PER_PAGE):
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

            if is_job_id_exists(job_id, SOURCE):
                print(f"Job {index + 1}: job_id {job_id} already in DB, skip click")
                continue

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
            print(f"Job {index + 1}: description length {len(job_desc_text)}")

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
    next_btn = page.locator('button[aria-label="View next page"]')
    if next_btn.count() == 0 or not next_btn.first.is_enabled():
        print("No next-page button, stop paging")
        return False
    next_btn.first.scroll_into_view_if_needed()
    pause(0.4, 0.8)
    next_btn.first.click()
    pause(5, 10, "Waiting after pagination")
    return True


def scrape_keyword(page, keyword, max_pages=DEFAULT_MAX_PAGES, max_jobs_per_page=MAX_JOBS_PER_PAGE):
    print(f"\n========== Keyword: {keyword} ==========")
    page.goto(jobs_search_url(keyword), wait_until="domcontentloaded")
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


def is_cdp_open():
    try:
        with socket.create_connection((CDP_HOST, CDP_PORT), timeout=1):
            return True
    except OSError:
        return False


def start_debug_chrome():
    """Launch a separate Chrome with remote debugging. Does not reuse the everyday Chrome window."""
    print(
        f"Nothing is listening on {CDP_URL}. "
        "Starting Chrome with remote debugging..."
    )
    subprocess.Popen(
        [
            CHROME_BIN,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={CHROME_USER_DATA_DIR}",
            "--no-first-run",
            "--no-default-browser-check",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        if is_cdp_open():
            print("Chrome remote debugging is ready.")
            return
        time.sleep(0.5)
    raise RuntimeError(
        f"Could not connect to {CDP_URL}. Start Chrome yourself with:\n"
        f'  "{CHROME_BIN}" --remote-debugging-port={CDP_PORT} '
        f'--user-data-dir="{CHROME_USER_DATA_DIR}"\n'
        "Log in to LinkedIn in that window, then run scraper.py again."
    )


def connect_browser(playwright):
    if not is_cdp_open():
        start_debug_chrome()
    try:
        browser = playwright.chromium.connect_over_cdp(CDP_URL)
    except Exception as e:
        raise RuntimeError(
            f"Playwright could not attach to Chrome at {CDP_URL}: {e}\n"
            "If a normal Chrome is already open, this debug instance must use "
            f"--user-data-dir={CHROME_USER_DATA_DIR}."
        ) from e
    if not browser.contexts:
        raise RuntimeError("Chrome opened, but no browser context was found.")
    return browser


def main():
    args = parse_args()
    keywords = args.keywords
    max_pages = args.max_pages
    print(f"Keywords: {keywords}")
    print(f"Max pages per keyword: {max_pages}")

    init_db()
    all_jobs = []

    with sync_playwright() as playwright:
        browser = connect_browser(playwright)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        print("Log in to LinkedIn in the debug Chrome window if you have not already.")

        for i, keyword in enumerate(keywords):
            jobs = scrape_keyword(page, keyword, max_pages=max_pages)
            all_jobs.extend(jobs)
            if i < len(keywords) - 1:
                pause(15, 30, "Rest between keywords")

        # Do not close the connected Chrome; it is the user's real session.

    print(f"\nDone. Saved {len(all_jobs)} new jobs this run.")


if __name__ == "__main__":
    main()
