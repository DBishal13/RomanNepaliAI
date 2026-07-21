# RomanNepaliAI

A small project to translate Nepali (Devanagari) to English for subtitles and general text. The goal is to support translating songs, skits, movies, and other content to help non-Nepali speakers understand the material.

This commit bootstraps a minimal Python package and a pluggable translation CLI.

What was added:
- src/roman_nepali_ai: package with a translation wrapper and CLI
- tests/: basic pytest verifying the stub translation behavior
- requirements.txt: optional deps for the Hugging Face backend
- .gitignore

Usage:
- Stub (no dependencies):
  python -m roman_nepali_ai.cli "नेपाल"
  (returns input unchanged)

- Hugging Face backend (optional, better quality):
  1) Install dependencies: pip install -r requirements.txt
  2) Run: python -m roman_nepali_ai.cli "नेपाल" --backend hf --model Helsinki-NLP/opus-mt-ne-en

Notes:
- If the HF backend is selected but transformers or the model are not available, the CLI prints an error and returns the input unchanged.
- Next work: implement subtitle pipeline (batch processing, SRT generation, time alignment), improve normalization for songs (line breaks, punctuation), and add CI.

Subtitle pipeline usage example:

- Translate an SRT file (stub backend):
  python -m roman_nepali_ai.cli --srt-in examples/imported_romanized_nepali/sample.srt --srt-out out.srt

- Translate with Google Translate (requires googletrans):
  pip install googletrans==4.0.0rc1
  python -m roman_nepali_ai.cli --srt-in examples/imported_romanized_nepali/sample.srt --srt-out out.srt --backend google

- Translate with Hugging Face model (optional):
  pip install -r requirements.txt
  python -m roman_nepali_ai.cli --srt-in examples/imported_romanized_nepali/sample.srt --srt-out out.srt --backend hf --model Helsinki-NLP/opus-mt-ne-en

- Subtitle normalization:
  By default the CLI normalizes translated subtitles (wraps long lines and merges very short captions). Use --no-normalize to disable this behavior:
  python -m roman_nepali_ai.cli --srt-in in.srt --srt-out out.srt --backend hf --no-normalize
