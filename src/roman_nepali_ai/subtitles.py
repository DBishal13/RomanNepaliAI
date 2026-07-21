"""Subtitle utilities: parse SRT, translate, and write translated SRT files.

Functions:
- parse_srt(path) -> list of dicts {index, start, end, text}
- write_srt(captions, path)
- translate_srt(in_path, out_path, backend='stub', model_name=None, normalize=True)

Supports three backends:
- 'stub' : returns input unchanged
- 'google' : uses googletrans (if installed)
- 'hf' : uses the Translator class (Hugging Face Marian) from translate.py

Also provides simple subtitle normalization (line wrapping and optional merging)
which helps produce readable subtitle lines for translation output.
"""
from typing import List, Dict, Optional
import re
import os

from .translate import Translator


_TIME_RE = re.compile(r"(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})")


def parse_srt(path: str) -> List[Dict]:
    """Parse a simple SRT file into caption dicts."""
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    if not content:
        return []

    blocks = re.split(r"\n\s*\n", content)
    captions = []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 2:
            continue
        # First line may be index; second line must be time
        time_line = lines[1] if _TIME_RE.search(lines[1]) else lines[0]
        m = _TIME_RE.search(time_line)
        if not m:
            # try to find time line anywhere
            found = False
            for ln in lines:
                m = _TIME_RE.search(ln)
                if m:
                    found = True
                    break
            if not found:
                continue
        start, end = m.group(1), m.group(2)
        # Text is the lines after the time line
        # locate index of time line
        try:
            idx = lines.index(time_line)
            text_lines = lines[idx+1:]
        except ValueError:
            # fallback: everything after second line
            text_lines = lines[2:]
        text = '\n'.join(text_lines).strip()
        # index detection
        try:
            index = int(lines[0])
        except Exception:
            index = len(captions) + 1
        captions.append({'index': index, 'start': start, 'end': end, 'text': text})
    return captions


def write_srt(captions: List[Dict], path: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        for c in captions:
            f.write(f"{c['index']}\n")
            f.write(f"{c['start']} --> {c['end']}\n")
            f.write(f"{c['text']}\n\n")


def _translate_texts_google(texts: List[str]) -> List[str]:
    try:
        from googletrans import Translator as GT
    except Exception as e:
        raise RuntimeError("googletrans is not available. Install with: pip install googletrans==4.0.0rc1")
    t = GT()
    out = []
    for txt in texts:
        try:
            res = t.translate(txt, src='ne', dest='en')
            out.append(res.text)
        except Exception:
            out.append(txt)
    return out


# Simple text wrapping utility
def _wrap_text(text: str, max_width: int = 40) -> str:
    words = text.split()
    if not words:
        return text
    lines = []
    cur = words[0]
    for w in words[1:]:
        if len(cur) + 1 + len(w) <= max_width:
            cur = cur + ' ' + w
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return '\n'.join(lines)


def normalize_subtitles(captions: List[Dict], max_width: int = 40, min_merge_len: int = 20) -> List[Dict]:
    """Wrap lines to max_width and merge very short adjacent captions.

    This modifies timing of merged captions (start from first, end from last).
    It returns a new list of captions.
    """
    # First wrap each caption's text
    wrapped = []
    for c in captions:
        text = c.get('text', '')
        # Preserve existing newlines by collapsing then wrapping
        joined = ' '.join(line.strip() for line in text.splitlines())
        new_text = _wrap_text(joined, max_width=max_width)
        new = c.copy()
        new['text'] = new_text
        wrapped.append(new)

    # Merge adjacent short captions
    merged = []
    for c in wrapped:
        if merged and len(merged[-1]['text'].replace('\n', ' ')) < min_merge_len:
            # attempt merge
            prev = merged[-1]
            combined_text = prev['text'].replace('\n', ' ') + ' ' + c['text'].replace('\n', ' ')
            if len(combined_text) <= max_width * 2:
                # merge into prev
                prev['text'] = _wrap_text(combined_text, max_width=max_width)
                prev['end'] = c['end']
                continue
        merged.append(c.copy())
    # Reindex
    for i, c in enumerate(merged, start=1):
        c['index'] = i
    return merged


def translate_srt(in_path: str, out_path: str, backend: str = 'stub', model_name: Optional[str] = None, normalize: bool = True) -> None:
    captions = parse_srt(in_path)
    if not captions:
        # write empty file
        open(out_path, 'w', encoding='utf-8').close()
        return

    texts = [c['text'] for c in captions]
    translated = []
    if backend == 'stub':
        translated = texts
    elif backend == 'google':
        translated = _translate_texts_google(texts)
    elif backend == 'hf':
        t = Translator(backend='hf', model_name=model_name)
        if not t.available:
            raise RuntimeError(f"HF backend unavailable: {t._load_error}")
        translated = [t.translate(t_txt) for t_txt in texts]
    else:
        raise ValueError('Unknown backend')

    # Replace texts and write
    new_caps = []
    for c, tr in zip(captions, translated):
        new = c.copy()
        new['text'] = tr
        new_caps.append(new)

    # Optionally normalize (wrap/merge) the translated output
    if normalize:
        new_caps = normalize_subtitles(new_caps)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    write_srt(new_caps, out_path)
