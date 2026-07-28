"""Configuration for the Nepal social-media scraper."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional


@dataclass
class ScraperConfig:
    output_dir: str = "scraped_data"

    num_tweets: int = 200
    num_reddit_posts: int = 150
    num_facebook_posts: int = 100

    lookback_days: int = 730

    keywords: List[str] = field(default_factory=lambda: [
        "nepal", "kathmandu", "pokhara", "chitwan", "dharan", "biratnagar",
        "nepali", "dashain", "tihar", "holi", "buddha jayanti",
        "sagarmatha", "everest", "annapurna", "langtang",
        "momo", "dal bhat", "gundruk", "dhido",
        "namaste", "dhanyabad", "mitho", "ramro",
    ])

    subreddits: List[str] = field(default_factory=lambda: [
        "Nepal", "nepalibloggers", "nepali", "KathmanduLiving",
        "NepalTourism", "NepalFood", "SouthAsia",
    ])

    facebook_pages: List[str] = field(default_factory=lambda: [
        "visitnepal2020", "kathmandupost", "nepaltimes", "nepalitimes",
    ])

    news_sites: List[str] = field(default_factory=lambda: [
        "https://kathmandupost.com",
        "https://myrepublica.nagariknetwork.com",
        "https://thehimalayantimes.com",
    ])

    reddit_client_id: Optional[str] = field(default_factory=lambda: os.environ.get("REDDIT_CLIENT_ID"))
    reddit_client_secret: Optional[str] = field(default_factory=lambda: os.environ.get("REDDIT_CLIENT_SECRET"))
    reddit_user_agent: str = "roman_nepali_ai_scraper/1.0"

    @property
    def start_date(self) -> datetime:
        return datetime.now() - timedelta(days=self.lookback_days)
