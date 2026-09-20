from urllib.parse import quote_plus
import argparse
import random
import socket
import sqlite3
import subprocess
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from db import init_db, save_job

CDP_HOST = "127.0.0.1"
CDP_PORT = 9222
CDP_URL = f"http://{CDP_HOST}:{CDP_PORT}"
CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CHROME_USER_DATA_DIR = "/tmp/chrome_selenium"

# de.indeed.com, posted within the last day (fromage=1).
BASE_URL = "https://de.indeed.com/jobs"
FROMAGE = "1"
DEFAULT_KEYWORDS = [
    "frontend",
    "full stack",
    "full-stack",
    "fullstack",
    "ai engineer",
    "product engineer",
    "software engineer",
]
DEFAULT_MAX_PAGES = 3
MAX_JOBS_PER_PAGE = 30
SOURCE = "indeed"
JOB_CARD_SELECTOR = ".mainContentTable"
JOB_TITLE_SELECTOR = "h3.jobTitle"
DETAIL_SELECTOR = '[data-testid="viewjob-main-content"]'
# Indeed SERP uses start=0, 10, 20, ...
RESULTS_PER_PAGE = 10


def pause(min_seconds, max_seconds, message=None):
    """Sleep a random interval to look less like a bot."""
    delay = random.uniform(min_seconds, max_seconds)
    if message:
        print(f"{message} ({delay:.1f}s)")
    time.sleep(delay)


def is_job_id_exists_in_db(job_id, source=SOURCE):
    """Return True if this job_id is already stored for the given source."""
    try:
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE job_id = ? AND source = ?",
            (job_id, source),
        )
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"Failed to check job_id {job_id} in DB: {e}")
        return False


def jobs_search_url(keyword, start=0):
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


def safe_text(locator, timeout=3000):
    try:
        if locator.count() == 0:
            return ""
        return (locator.first.inner_text(timeout=timeout) or "").strip()
    except Exception:
        return ""


def safe_attr(locator, name, timeout=3000):
    try:
        if locator.count() == 0:
            return ""
        return locator.first.get_attribute(name, timeout=timeout) or ""
    except Exception:
        return ""


def parse_args():
    parser = argparse.ArgumentParser(description="Scrape Indeed DE jobs into SQLite.")
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


def extract_card_fields(card):
    """Read title and job_id from an Indeed result card."""
    title_heading = card.locator(JOB_TITLE_SELECTOR).first
    title = safe_text(title_heading.locator("span"))
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

            if is_job_id_exists_in_db(job_id):
                print(f"Job {index + 1}: job_id {job_id} already in DB, skip click")
                continue

            card.click()
            page.wait_for_selector(DETAIL_SELECTOR, timeout=15000)
            pause(1.0, 2.0)

            detail = page.locator(DETAIL_SELECTOR).first
            description_html = detail.inner_html(timeout=10000) or ""
            print(f"Job {index + 1}: description html length {len(description_html)}")

            # Indeed JD is rich HTML without stable field classes; store full HTML.
            # company / location / applicants are left empty for now.
            job_data = {
                "title": title,
                "company": "",
                "location": "",
                "status": "new",
                "link": href_value,
                "job_id": job_id,
                "applicants": "",
                "description": description_html,
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


def scrape_keyword(page, keyword, max_pages=DEFAULT_MAX_PAGES, max_jobs_per_page=MAX_JOBS_PER_PAGE):
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


def is_cdp_open():
    try:
        with socket.create_connection((CDP_HOST, CDP_PORT), timeout=1):
            return True
    except OSError:
        return False


def start_debug_chrome():
    """Launch a separate Chrome with remote debugging."""
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
        "Open Indeed in that window if needed, then run indeed_scraper.py again."
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
    print(f"Source: {SOURCE}")
    print(f"Keywords: {keywords}")
    print(f"Max pages per keyword: {max_pages}")

    init_db()
    all_jobs = []

    with sync_playwright() as playwright:
        browser = connect_browser(playwright)
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else context.new_page()
        print("Use the debug Chrome window. Dismiss Indeed cookie banners if prompted.")

        for i, keyword in enumerate(keywords):
            jobs = scrape_keyword(page, keyword, max_pages=max_pages)
            all_jobs.extend(jobs)
            if i < len(keywords) - 1:
                pause(15, 30, "Rest between keywords")

    print(f"\nDone. Saved {len(all_jobs)} new Indeed jobs this run.")


if __name__ == "__main__":
    main()
