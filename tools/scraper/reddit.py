"""Reddit scraping.

Two backends:
- PRAW, which needs a registered Reddit app (set REDDIT_CLIENT_ID /
  REDDIT_CLIENT_SECRET env vars -- Reddit's API has required real app
  credentials since 2023; there is no anonymous PRAW mode anymore).
- A no-auth fallback that hits Reddit's public `.json` endpoints
  directly. Reddit has increasingly rate-limited/blocked this path for
  non-browser user agents, so it's not guaranteed either.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime

import requests

from .config import ScraperConfig
from .text_utils import clean_text, is_romanized_nepali

logger = logging.getLogger(__name__)

try:
    import praw
    PRAW_AVAILABLE = True
except ImportError:
    praw = None
    PRAW_AVAILABLE = False


def _matches(text: str, config: ScraperConfig) -> bool:
    return is_romanized_nepali(text) or any(k in text.lower() for k in config.keywords)


def scrape_reddit_praw(config: ScraperConfig) -> list:
    if not PRAW_AVAILABLE:
        logger.warning("praw not installed; skipping PRAW Reddit backend")
        return []
    if not (config.reddit_client_id and config.reddit_client_secret):
        logger.warning("REDDIT_CLIENT_ID/REDDIT_CLIENT_SECRET not set; skipping PRAW Reddit backend")
        return []

    reddit = praw.Reddit(
        client_id=config.reddit_client_id,
        client_secret=config.reddit_client_secret,
        user_agent=config.reddit_user_agent,
    )

    results: list = []
    per_sub = max(5, config.num_reddit_posts // max(1, len(config.subreddits)))
    for sub_name in config.subreddits:
        if len(results) >= config.num_reddit_posts:
            break
        try:
            for post in reddit.subreddit(sub_name).hot(limit=per_sub):
                text = clean_text(f"{post.title} {post.selftext}".strip())
                if not (10 <= len(text) <= 1000) or not _matches(text, config):
                    continue
                results.append({
                    "date": datetime.fromtimestamp(post.created_utc),
                    "text": text,
                    "user": str(post.author) if post.author else "Unknown",
                    "source": "Reddit",
                    "subreddit": sub_name,
                    "platform_id": post.id,
                    "url": f"https://reddit.com{post.permalink}",
                    "score": post.score,
                    "num_comments": post.num_comments,
                })
        except Exception:
            logger.exception("PRAW failed for r/%s", sub_name)
            continue
        time.sleep(2)

    logger.info("Reddit (PRAW): collected %d posts", len(results))
    return results


def scrape_reddit_public_json(config: ScraperConfig) -> list:
    headers = {"User-Agent": config.reddit_user_agent}
    results: list = []

    for sub_name in config.subreddits:
        if len(results) >= config.num_reddit_posts:
            break
        try:
            resp = requests.get(
                f"https://www.reddit.com/r/{sub_name}/hot.json?limit=25",
                headers=headers, timeout=10,
            )
            resp.raise_for_status()
            for child in resp.json().get("data", {}).get("children", []):
                post = child.get("data", {})
                text = clean_text(f"{post.get('title', '')} {post.get('selftext', '')}".strip())
                if len(text) < 10 or not _matches(text, config):
                    continue
                results.append({
                    "date": datetime.fromtimestamp(post.get("created_utc", time.time())),
                    "text": text,
                    "user": post.get("author", "Unknown"),
                    "source": "Reddit",
                    "subreddit": sub_name,
                    "platform_id": post.get("id", ""),
                    "url": f"https://reddit.com{post.get('permalink', '')}",
                    "score": post.get("score", 0),
                    "num_comments": post.get("num_comments", 0),
                })
        except Exception:
            logger.exception("Public JSON fetch failed for r/%s", sub_name)
            continue
        time.sleep(2)

    logger.info("Reddit (public JSON): collected %d posts", len(results))
    return results


def scrape_reddit(config: ScraperConfig) -> list:
    results = scrape_reddit_praw(config)
    if len(results) < config.num_reddit_posts:
        results.extend(scrape_reddit_public_json(config))
    return results
