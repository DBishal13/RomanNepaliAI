"""Headline scraping from a couple of Nepal news sites, as extra volume
beyond the social platforms."""
from __future__ import annotations

import logging
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .config import ScraperConfig
from .text_utils import clean_text

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def scrape_news(config: ScraperConfig) -> list:
    results: list = []
    for site in config.news_sites:
        try:
            resp = requests.get(site, headers=_HEADERS, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "html.parser")
            for headline in soup.find_all(["h1", "h2", "h3"], limit=5):
                text = clean_text(headline.get_text().strip())
                if len(text) >= 15 and any(k in text.lower() for k in ("nepal", "kathmandu", "nepali")):
                    results.append({
                        "date": datetime.now(),
                        "text": text,
                        "user": "news_source",
                        "source": "Nepal_News",
                        "platform_id": f"news_{len(results)}",
                        "url": site,
                        "likes": 0, "comments": 0, "shares": 0,
                    })
        except Exception:
            logger.exception("News scrape failed for %s", site)
            continue
        time.sleep(2)

    logger.info("News: collected %d headlines", len(results))
    return results
