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
