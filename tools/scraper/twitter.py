"""Twitter/X scraping via snscrape.

snscrape works by reverse-engineering Twitter's web frontend rather than
an official API. Twitter/X has locked this down repeatedly since 2023,
so on a current install this will most likely return zero results --
kept as a reference implementation, not a guarantee it still works.
"""
from __future__ import annotations

import logging
import time

from .config import ScraperConfig
from .text_utils import clean_text, is_in_length_range, is_romanized_nepali

logger = logging.getLogger(__name__)

try:
    import snscrape.modules.twitter as sntwitter
    SNSCRAPE_AVAILABLE = True
except ImportError:
    sntwitter = None
    SNSCRAPE_AVAILABLE = False

_QUERIES = [
    "Nepal OR Kathmandu",
    "nepali food OR momo",
    "dashain OR tihar",
    "namaste Nepal",
    "Pokhara OR Chitwan",
    "Everest OR Annapurna",
]


def scrape_twitter(config: ScraperConfig) -> list:
    if not SNSCRAPE_AVAILABLE:
        logger.warning("snscrape not installed; skipping Twitter")
        return []

    per_query = max(10, config.num_tweets // len(_QUERIES))
    results: list = []

    for i, query in enumerate(_QUERIES):
        if len(results) >= config.num_tweets:
            break
        if i > 0:
            time.sleep(5)  # basic rate limiting between queries

        collected = 0
        try:
            for tweet in sntwitter.TwitterSearchScraper(query).get_items():
                if collected >= per_query or len(results) >= config.num_tweets:
                    break
                text = clean_text(getattr(tweet, "content", "") or "")
                if not is_in_length_range(text):
                    continue
                if not (is_romanized_nepali(text) or any(k in text.lower() for k in config.keywords)):
                    continue
                results.append({
                    "date": tweet.date,
                    "text": text,
                    "user": getattr(getattr(tweet, "user", None), "username", "unknown"),
                    "source": "Twitter",
                    "platform_id": str(getattr(tweet, "id", "")),
                    "url": getattr(tweet, "url", ""),
                    "retweets": getattr(tweet, "retweetCount", 0),
                    "likes": getattr(tweet, "likeCount", 0),
                })
                collected += 1
        except Exception:
            logger.exception("Twitter query failed: %s", query)
            continue

    logger.info("Twitter: collected %d posts", len(results))
    return results
