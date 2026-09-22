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

from config import (
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


def _to_plain_text(text: str) -> str:
    """Strip HTML tags/entities so language detection sees actual copy, not markup."""
    if not text:
        return ""
    cleaned = re.sub(
        r"<(style|script)[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html_module.unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def detect_job_detail_language(text: str):
    """
    Detect the primary language of job-detail content.

    Uses Lingua (Apache-2.0): statistical n-gram language models, not umlauts
    or a German word list. HTML is stripped first.

    Args:
        text: Job description / detail HTML or plain text

    Returns:
        Lowercase ISO 639-1 code such as 'de' or 'en', or None if unknown.
    """
    plain = _to_plain_text(text)
    if len(plain) < _MIN_LANG_CHARS:
        return None
    language = _get_language_detector().detect_language_of(plain)
    if language is None:
        return None
    return language.iso_code_639_1.name.lower()


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
