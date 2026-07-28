"""Text filtering/cleaning helpers shared by every scraper backend."""
from __future__ import annotations

import re

_NEPALI_INDICATORS = [
    "ma", "timi", "hami", "uniharu", "yo", "tyo", "yaha", "tyaha",
    "ghar", "khana", "pani", "paisa", "ramro", "mitho", "thulo", "sano",
    "daju", "didi", "ama", "baba", "bahini", "bhai",
    "namaste", "dhanyabad", "kasto", "kata", "kina", "kasari",
    "gardai", "garchu", "garne", "bhanne", "huncha", "thiyo",
    "cha", "chha", "xaina", "xan", "xa", "hun", "haina",
    "lai", "ko", "ka", "ki", "le", "bata", "samma",
    "chu", "chau", "chan", "chhau", "chhan",
    "dai", "ra", "ani", "tara", "kinabhane",
    "nepal", "kathmandu", "pokhara", "dashain", "tihar",
    "momo", "dalbhat", "gundruk", "sel", "roti",
]

_ENGLISH_INDICATORS = [
    "the", "and", "for", "are", "but", "not", "you", "all", "can", "had",
    "her", "was", "one", "our", "out", "day", "get", "has", "him", "his",
    "how", "its", "may", "new", "now", "old", "see", "two", "who", "boy",
    "did", "she", "use", "way", "why",
]

_URL_RE = re.compile(r"http[s]?://\S+")
_MENTION_RE = re.compile(r"@[A-Za-z0-9_]+")
_HASHTAG_RE = re.compile(r"#([A-Za-z0-9_]+)")
_WHITESPACE_RE = re.compile(r"\s+")
_NON_BASIC_RE = re.compile(r"[^\w\s.,!?-]")


def is_romanized_nepali(text: str) -> bool:
    """Heuristic only: more Nepali-word hits than English-word hits, and at least 2.

    False positives/negatives are expected -- this is a cheap pre-filter,
    not a language classifier.
    """
    if not text or len(text.strip()) < 3:
        return False
    text = text.lower().strip()
    nepali_hits = sum(1 for w in _NEPALI_INDICATORS if w in text)
    english_hits = sum(1 for w in _ENGLISH_INDICATORS if f" {w} " in f" {text} ")
    return nepali_hits > english_hits and nepali_hits >= 2


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = _URL_RE.sub("", text)
    text = _MENTION_RE.sub("", text)
    text = _HASHTAG_RE.sub(r"\1", text)
    text = _WHITESPACE_RE.sub(" ", text)
    text = _NON_BASIC_RE.sub("", text)
    return text.strip()


def is_in_length_range(text: str, min_length: int = 10, max_length: int = 500) -> bool:
    return min_length <= len(text) <= max_length
