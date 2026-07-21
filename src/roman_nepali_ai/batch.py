"""Batch processing utilities for SRT translation.

Functions:
- process_srt_folder(in_dir, out_dir, backend='stub', model_name=None, pattern='*.srt')
"""
from pathlib import Path
from typing import Optional
import fnmatch

from .subtitles import translate_srt


def process_srt_folder(in_dir: str, out_dir: str, backend: str = 'stub', model_name: Optional[str] = None, pattern: str = '*.srt') -> int:
    """Translate all SRT files from in_dir into out_dir using the given backend.

    Returns the number of files processed.
    """
    src = Path(in_dir)
    dst = Path(out_dir)
    if not src.exists() or not src.is_dir():
        raise ValueError(f"Input directory does not exist: {in_dir}")
    dst.mkdir(parents=True, exist_ok=True)

    files = [p for p in src.iterdir() if p.is_file() and fnmatch.fnmatch(p.name, pattern)]
    for p in files:
        out_path = dst / p.name
        translate_srt(str(p), str(out_path), backend=backend, model_name=model_name)
    return len(files)
