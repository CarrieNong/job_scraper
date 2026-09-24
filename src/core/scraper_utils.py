"""
Shared utility functions for web scrapers.
Provides common functionality for browser automation, delays, and data extraction.
"""
import argparse
import html as html_module
import random
import re
import socket
import subprocess
import time

from lingua import Language, LanguageDetectorBuilder

from core.config import (
    DEFAULT_KEYWORDS,
    DEFAULT_MAX_PAGES,
    CDP_HOST,
    CDP_PORT,
    CDP_URL,
    CHROME_BIN,
    CHROME_USER_DATA_DIR,
    TITLE_EXCLUDE_KEYWORDS,
)

# Pre-compile all exclusion patterns once for efficiency (case-insensitive)
_EXCLUDE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in TITLE_EXCLUDE_KEYWORDS]

# Too little text to classify reliably (failed/empty detail panels).
_MIN_LANG_CHARS = 40

# Ignore tiny fragments ("Berlin", "3.8") when estimating language share.
_MIN_CHUNK_CHARS = 12

# Indeed DE chrome ("Weiter zur Bewerbung") is a few German lines on an
# English JD. Only treat the posting as German above this share.
GERMAN_SHARE_THRESHOLD = 0.20

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?。！？])\s+|\n+")

# Restrict the model set to languages commonly seen on DE job boards.
# Lingua is more accurate with a small candidate set than with all 75 languages.
_LANGUAGE_DETECTOR = None


def is_title_excluded(title: str) -> bool:
    """
    Return True if the job title matches any exclusion pattern defined in
    TITLE_EXCLUDE_KEYWORDS, meaning the job card should be skipped without
    clicking into the detail page.

    Args:
        title: Job title string extracted from the card

    Returns:
        True if the title should be excluded, False otherwise
    """
    if not title:
        return False
    for pattern in _EXCLUDE_PATTERNS:
        if pattern.search(title):
            return True
    return False


def _get_language_detector():
    """Build a Lingua detector once; language models load lazily on first use."""
    global _LANGUAGE_DETECTOR
    if _LANGUAGE_DETECTOR is None:
        _LANGUAGE_DETECTOR = LanguageDetectorBuilder.from_languages(
            Language.ENGLISH,
            Language.GERMAN,
            Language.FRENCH,
            Language.DUTCH,
        ).build()
    return _LANGUAGE_DETECTOR


def strip_html(html_text: str) -> str:
    """
    Convert raw HTML to readable plain text.

    Removes style/script blocks and tags, decodes entities, and keeps
    paragraph/list breaks so the saved JD stays scannable.
    """
    if not html_text:
        return ""
    text = re.sub(
        r"<(style|script)[^>]*>.*?</\1>",
        "",
        html_text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    text = re.sub(r"<(br|p|li|h[1-6]|div|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = html_module.unescape(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [line.strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def german_content_share(text: str) -> float:
    """
    Fraction of classified text that Lingua labels as German (0.0–1.0).

    Splits on sentences/lines and weights each chunk by character length.
    HTML is stripped first. Returns 0.0 when there is too little text.
    """
    plain = strip_html(text)
    if len(plain) < _MIN_LANG_CHARS:
        return 0.0

    chunks = [
        chunk.strip()
        for chunk in _SENTENCE_SPLIT.split(plain)
        if len(chunk.strip()) >= _MIN_CHUNK_CHARS
    ]
    if not chunks:
        return 0.0

    detector = _get_language_detector()
    german_chars = 0
    total_chars = 0
    for chunk in chunks:
        language = detector.detect_language_of(chunk)
        total_chars += len(chunk)
        if language == Language.GERMAN:
            german_chars += len(chunk)
    if total_chars == 0:
        return 0.0
    return german_chars / total_chars


def detect_job_detail_language(text: str):
    """
    Detect job-detail language.

    Uses Lingua (Apache-2.0) n-gram models. Classified as German only when
    more than GERMAN_SHARE_THRESHOLD of the text is German, so a few DE UI
    strings on an English Indeed page do not count.

    Args:
        text: Job description HTML or plain text

    Returns:
        Tuple of (iso_code or None, german_share from 0.0 to 1.0).
        iso_code is a lowercase ISO 639-1 code such as 'de' or 'en'.
    """
    plain = strip_html(text)
    if len(plain) < _MIN_LANG_CHARS:
        return None, 0.0

    german_share = german_content_share(plain)
    if german_share > GERMAN_SHARE_THRESHOLD:
        return "de", german_share

    language = _get_language_detector().detect_language_of(plain)
    if language is None:
        return None, german_share
    return language.iso_code_639_1.name.lower(), german_share


def pause(min_seconds, max_seconds, message=None):
    """
    Sleep for a random interval to simulate human behavior.
    
    Args:
        min_seconds: Minimum delay in seconds
        max_seconds: Maximum delay in seconds
        message: Optional message to print with the delay time
    """
    delay = random.uniform(min_seconds, max_seconds)
    if message:
        print(f"{message} ({delay:.1f}s)")
    time.sleep(delay)


def safe_text(locator, timeout=3000):
    """
    Safely extract text content from a Playwright locator.
    Returns empty string if element not found or any error occurs.
    
    Args:
        locator: Playwright locator object
        timeout: Timeout in milliseconds
        
    Returns:
        Stripped text content or empty string
    """
    try:
        if locator.count() == 0:
            return ""
        return (locator.first.inner_text(timeout=timeout) or "").strip()
    except Exception:
        return ""


def safe_attr(locator, name, timeout=3000):
    """
    Safely extract an attribute value from a Playwright locator.
    Returns empty string if element not found or any error occurs.
    
    Args:
        locator: Playwright locator object
        name: Attribute name to extract
        timeout: Timeout in milliseconds
        
    Returns:
        Attribute value or empty string
    """
    try:
        if locator.count() == 0:
            return ""
        return locator.first.get_attribute(name, timeout=timeout) or ""
    except Exception:
        return ""


def parse_args():
    """
    Parse command-line arguments for the scraper.
    
    Returns:
        Parsed arguments with keywords and max_pages
    """
    parser = argparse.ArgumentParser(description="Scrape job listings into MongoDB.")
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


def is_cdp_open():
    """
    Check if Chrome DevTools Protocol port is accessible.
    
    Returns:
        True if CDP port is open, False otherwise
    """
    try:
        with socket.create_connection((CDP_HOST, CDP_PORT), timeout=1):
            return True
    except OSError:
        return False


def start_debug_chrome(site_name="the website"):
    """
    Launch Chrome with remote debugging enabled.
    Uses a separate user data directory to avoid conflicts with regular Chrome.
    
    Args:
        site_name: Name of the website for error messages
        
    Raises:
        RuntimeError: If Chrome fails to start or CDP connection fails
    """
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
        f"Open {site_name} in that window if needed, then run the scraper again."
    )


def open_scraper_page(context, bring_to_front=False):
    """
    Open a dedicated tab for one scraper.

    Parallel scrapers must not share context.pages[0]. A second page.goto on
    the same tab aborts the first navigation (net::ERR_ABORTED), so LinkedIn
    never finishes loading when Indeed starts at the same time.
    """
    page = context.new_page()
    if bring_to_front:
        try:
            page.bring_to_front()
        except Exception:
            pass
    return page


def goto_page(page, url, wait_until="domcontentloaded", attempts=3, timeout=60000):
    """
    Navigate, retrying when Chrome aborts the load.

    LinkedIn often replaces the original request with a redirect. Playwright
    reports that as net::ERR_ABORTED even if the destination later commits.
    """
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            page.goto(url, wait_until=wait_until, timeout=timeout)
            return
        except Exception as e:
            last_error = e
            aborted = "ERR_ABORTED" in str(e)
            if aborted:
                try:
                    current = page.url or ""
                except Exception:
                    current = ""
                if current and current != "about:blank" and "linkedin.com" in current:
                    print(f"Navigation aborted, continuing at {current}")
                    return
            if not aborted or attempt == attempts:
                raise
            print(f"Navigation aborted (attempt {attempt}/{attempts}), retrying...")
            time.sleep(2)
    raise last_error


def connect_browser(playwright, site_name="the website"):
    """
    Connect to Chrome via Chrome DevTools Protocol.
    Starts Chrome with debugging if not already running.
    
    Args:
        playwright: Playwright instance
        site_name: Name of the website for error messages
        
    Returns:
        Connected browser instance
        
    Raises:
        RuntimeError: If connection fails or no browser context found
    """
    if not is_cdp_open():
        start_debug_chrome(site_name)
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
