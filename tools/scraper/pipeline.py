"""Combine, dedupe, and save results from the individual scraper backends."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Optional

import pandas as pd

from .config import ScraperConfig

logger = logging.getLogger(__name__)


def combine(*result_lists: list) -> Optional[pd.DataFrame]:
    all_data = [row for results in result_lists for row in results]
    if not all_data:
        return None

    df = pd.DataFrame(all_data)
    df["_key"] = df["text"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["_key"]).drop(columns=["_key"])
    df = df.sort_values("date", ascending=False)
    df["text_length"] = df["text"].str.len()
    df["word_count"] = df["text"].str.split().str.len()
    df["scraped_at"] = datetime.now()
    return df


def summarize(df: pd.DataFrame) -> dict:
    return {
        "total_records": len(df),
        "by_source": df["source"].value_counts().to_dict(),
        "date_range": {
            "earliest": df["date"].min().strftime("%Y-%m-%d"),
            "latest": df["date"].max().strftime("%Y-%m-%d"),
        },
        "text_stats": {
            "avg_length": float(df["text_length"].mean()),
            "avg_words": float(df["word_count"].mean()),
            "min_length": int(df["text_length"].min()),
            "max_length": int(df["text_length"].max()),
        },
    }


def save(df: pd.DataFrame, summary: dict, config: ScraperConfig) -> None:
    os.makedirs(config.output_dir, exist_ok=True)

    csv_path = os.path.join(config.output_dir, "romanized_nepali_dataset.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8")

    json_path = os.path.join(config.output_dir, "romanized_nepali_dataset.json")
    df_json = df.copy()
    df_json["date"] = df_json["date"].astype(str)
    df_json["scraped_at"] = df_json["scraped_at"].astype(str)
    df_json.to_json(json_path, orient="records", indent=2, force_ascii=False)

    summary_path = os.path.join(config.output_dir, "scraping_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Saved %d records to %s", len(df), config.output_dir)
