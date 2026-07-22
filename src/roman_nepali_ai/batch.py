"""Batch processing utilities for SRT translation.

Functions:
- process_srt_folder(in_dir, out_dir, backend='stub', model_name=None, pattern='*.srt', src='ne', tgt='en')
"""
from pathlib import Path
from typing import Optional
import fnmatch

from .subtitles import translate_srt


def process_srt_folder(in_dir: str, out_dir: str, backend: str = 'stub', model_name: Optional[str] = None,
                        pattern: str = '*.srt', src: str = 'ne', tgt: str = 'en') -> int:
    """Translate all SRT files from in_dir into out_dir using the given backend.

    Returns the number of files processed.
    """
    src_dir = Path(in_dir)
    dst_dir = Path(out_dir)
    if not src_dir.exists() or not src_dir.is_dir():
        raise ValueError(f"Input directory does not exist: {in_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)

    files = [p for p in src_dir.iterdir() if p.is_file() and fnmatch.fnmatch(p.name, pattern)]
    for p in files:
        out_path = dst_dir / p.name
        translate_srt(str(p), str(out_path), backend=backend, model_name=model_name, src=src, tgt=tgt)
    return len(files)
