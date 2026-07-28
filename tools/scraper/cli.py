"""Entry point: run every backend and save whatever real data comes back.

Unlike the notebook this was ported from, this does NOT fall back to
generating fake sample posts when scraping yields nothing -- see
README.md in this directory for why. An empty result means the backends
genuinely didn't find anything, which, as of this writing, is the common
case (see README.md's "Honest limitations").
"""
from __future__ import annotations

import argparse
import logging

from .config import ScraperConfig
from .facebook import scrape_facebook, scrape_facebook_fallback
from .news import scrape_news
from .pipeline import combine, save, summarize
from .reddit import scrape_reddit
from .twitter import scrape_twitter


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Nepal-related social posts")
    parser.add_argument("--output-dir", default="scraped_data")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    config = ScraperConfig(output_dir=args.output_dir)

    twitter_data = scrape_twitter(config)
    reddit_data = scrape_reddit(config)
    facebook_data = scrape_facebook(config) or scrape_facebook_fallback(config)
    news_data = scrape_news(config)

    df = combine(twitter_data, reddit_data, facebook_data, news_data)
    if df is None:
        print("No data collected from any backend.")
        return

    summary = summarize(df)
    save(df, summary, config)
    print(f"Saved {summary['total_records']} records to {config.output_dir}/")


if __name__ == "__main__":
    main()
