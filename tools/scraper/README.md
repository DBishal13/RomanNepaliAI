# Nepal social-media scraper (exploratory)

Ported and cleaned up from an earlier notebook that tried to build a
Romanized-Nepali training corpus by scraping Twitter/Reddit/Facebook.
Not currently used by the rest of this repo (transliteration is
rule-based, translation uses pluggable pretrained/API backends -- see
the top-level README's "Honest limitations"). Kept here in case there's
a future use for real Nepali social text (e.g. expanding the casual
transliteration dictionary, or evaluating translation backends against
real informal text).

## Install

```bash
pip install -e ".[scraper]"
```

## Run

```bash
python -m tools.scraper.cli --output-dir scraped_data -v
```

Reddit's PRAW backend needs a registered app:

```bash
export REDDIT_CLIENT_ID=...
export REDDIT_CLIENT_SECRET=...
```

Without those, only the no-auth Reddit fallback (public `.json`
endpoints) runs.

## Honest limitations

- **Twitter/X is very likely broken.** `snscrape` works by reverse-engineering
  Twitter's web frontend, not an official API, and Twitter/X has locked
  this down repeatedly since 2023. Expect zero results on a current
  install.
- **Facebook is fragile for the same reason.** `facebook-scraper` and the
  plain-HTML fallback both parse Facebook's mobile site, which changes
  without notice and increasingly requires login.
- **Reddit's no-auth JSON fallback gets rate-limited/blocked** for
  non-browser user agents on and off; the PRAW backend needs real API
  credentials (Reddit removed anonymous access years ago).
- **None of this is guaranteed to produce anything.** When the original
  notebook ran into that reality, it silently generated hardcoded
  "sample" posts and saved them as if they were scraped data (fake
  usernames, fake URLs like `twitter.com/enhanced/0`). This port
  **deliberately removes that behavior** -- an empty result here means
  the backends genuinely found nothing, not that the pipeline failed
  silently. `scraped_data/` at the repo root still contains that
  original notebook's synthetic output; treat it as example text, not
  real social-media data.
- The **global SSL-verification bypass** and `requests.Session` monkey-patch
  from the original notebook were also dropped -- disabling TLS
  verification process-wide is a real security anti-pattern, not
  something worth carrying forward even for a scraper.

## Layout

```
config.py       ScraperConfig (limits, keywords, subreddits, pages, credentials)
text_utils.py   clean_text(), is_romanized_nepali() heuristic filter
twitter.py      scrape_twitter() -- snscrape
reddit.py       scrape_reddit() -- PRAW + public-JSON fallback
facebook.py     scrape_facebook() -- facebook-scraper + HTML fallback
news.py         scrape_news() -- headline scrape of a few Nepal news sites
pipeline.py     combine() / summarize() / save() -- merge, dedupe, write CSV+JSON
cli.py          python -m tools.scraper.cli
```
