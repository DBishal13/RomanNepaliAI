"""Facebook scraping.

facebook-scraper works by parsing Facebook's mobile web frontend and
breaks whenever Facebook changes markup or requires a login wall --
treat this as unreliable. The fallback below (plain requests +
BeautifulSoup against the same mobile site) exists for the same reason:
there's no official free API for public page posts, so both paths are
scraping HTML that can change without notice.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .config import ScraperConfig
from .text_utils import clean_text, is_romanized_nepali

logger = logging.getLogger(__name__)

try:
    from facebook_scraper import get_posts
    FACEBOOK_SCRAPER_AVAILABLE = True
except ImportError:
    get_posts = None
    FACEBOOK_SCRAPER_AVAILABLE = False

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def _matches(text: str, config: ScraperConfig) -> bool:
    return is_romanized_nepali(text) or any(k in text.lower() for k in config.keywords)


def scrape_facebook(config: ScraperConfig) -> list:
    if not FACEBOOK_SCRAPER_AVAILABLE:
        logger.warning("facebook-scraper not installed; skipping Facebook")
        return []

    results: list = []
    per_page = max(3, config.num_facebook_posts // max(1, len(config.facebook_pages)))

    for page in config.facebook_pages:
        if len(results) >= config.num_facebook_posts:
            break
        page_count = 0
        try:
            for post in get_posts(page, pages=3, timeout=30, sleep=2):
                if page_count >= per_page or len(results) >= config.num_facebook_posts:
                    break
                text = clean_text(post.get("text", "") or "")
                if not (15 <= len(text) <= 800) or not _matches(text, config):
                    continue
                results.append({
                    "date": post.get("time", datetime.now()),
                    "text": text,
                    "user": page,
                    "source": "Facebook",
                    "platform_id": post.get("post_id", ""),
                    "url": post.get("post_url", ""),
                    "likes": post.get("likes", 0),
                    "comments": post.get("comments", 0),
                    "shares": post.get("shares", 0),
                })
                page_count += 1
        except Exception:
            logger.exception("Facebook scrape failed for page %s", page)
            continue
        time.sleep(5)

    logger.info("Facebook: collected %d posts", len(results))
    return results


def scrape_facebook_fallback(config: ScraperConfig) -> list:
    """Best-effort HTML scrape of the mobile Facebook site, used when
    facebook-scraper isn't installed or returns nothing."""
    results: list = []
    for page in config.facebook_pages[:2]:
        try:
            resp = requests.get(f"https://m.facebook.com/{page}", headers=_HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            for element in soup.find_all(["p", "div"], string=True)[:5]:
                text = clean_text(element.get_text().strip())
                if len(text) >= 15 and _matches(text, config):
                    results.append({
                        "date": datetime.now(),
                        "text": text,
                        "user": page,
                        "source": "Facebook",
                        "platform_id": f"alt_{len(results)}",
                        "url": f"https://m.facebook.com/{page}",
                        "likes": 0, "comments": 0, "shares": 0,
                    })
        except Exception:
            logger.exception("Facebook fallback failed for page %s", page)
            continue
        time.sleep(3)

    logger.info("Facebook (fallback): collected %d posts", len(results))
    return results
