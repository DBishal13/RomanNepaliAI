# RomanNepaliAI

Tools for working with Nepali text in three directions: **transliteration** (romanized Nepali &harr; Devanagari script, same language) and **translation** (Nepali &harr; English, different languages). Built for subtitles, texting-style Nepali, and general text, with a CLI, a web demo, and a small backend API.

## What's here

- **Transliteration** &mdash; deterministic, rule-based romanized-Nepali &rarr; Devanagari conversion, plus the reverse. Two modes:
  - **Formal**: a fixed, case-sensitive ITRANS/Harvard-Kyoto-style scheme (`t` vs `T` = dental vs retroflex, etc.) &mdash; no dictionary, purely rules.
  - **Casual**: tuned for free-typed texting-style Nepali (`"malai tha xaina"`) &mdash; a curated common-word dictionary, English-loanword passthrough, case-insensitive fallback.
- **Translation** &mdash; Nepali &harr; English, via pluggable backends:
  - `stub`: no-op passthrough (no dependencies, useful for testing the pipeline shape).
  - `google`: real translation via [deep-translator](https://github.com/nidhaloff/deep-translator)'s `GoogleTranslator`. Supports both directions (`--src ne --tgt en` or `--src en --tgt ne`).
  - `hf`: local inference via a Hugging Face MarianMT model (`Helsinki-NLP/opus-mt-ne-en` by default). Nepali&rarr;English only &mdash; it's a single fixed model, and asking it for the other direction raises a clear error rather than silently mistranslating.
- **Subtitle pipeline** &mdash; parse/translate/write `.srt` files, with normalization (line wrapping, merging very short captions) and batch processing over a whole folder.
- **Web demo** (`docs/`) &mdash; a static page (client-side transliteration, no server needed for that part) with an optional translation panel that calls the backend API. Includes voice input/output via the browser's Web Speech API (mic buttons for speech-to-text, speaker buttons for text-to-speech) where the browser supports it.
- **Backend API** (`src/roman_nepali_ai/server.py`) &mdash; a minimal FastAPI service exposing `Translator` over HTTP, so the static web demo can call real translation without embedding secrets client-side.

This is a rule/dictionary/API-composition system, not a trained model &mdash; see [Honest limitations](#honest-limitations) below.

## Install

```bash
pip install -e .                 # core (transliteration, stub backend, SRT pipeline)
pip install -e ".[google]"       # + real translation via deep-translator
pip install -e ".[hf]"           # + local Hugging Face MarianMT backend (heavier: transformers, torch)
pip install -e ".[server]"       # + FastAPI/uvicorn to run the backend API
pip install -e ".[dev]"          # + pytest/httpx for running the test suite
```

Extras compose, e.g. `pip install -e ".[dev,server]"` for development.

## CLI

Entry point: `roman-nepali-ai` (or `python -m roman_nepali_ai.cli`).

**Transliteration** (romanized Nepali &rarr; Devanagari, no translation):

```bash
python -m roman_nepali_ai.cli "malai tha xaina" --transliterate --casual
# मलाई था छैन

python -m roman_nepali_ai.cli "ghar" --transliterate
# घर्   (formal mode: no trailing vowel -> a "dead" consonant, by design)

python -m roman_nepali_ai.cli --transliterate --casual
# starts an interactive REPL; type romanized Nepali, Ctrl-D to exit
```

**Translation** (plain text, both directions):

```bash
python -m roman_nepali_ai.cli "मेरो नाम बिशाल हो" --backend google
# My name is Bishal

python -m roman_nepali_ai.cli "My name is Bishal" --backend google --src en --tgt ne
# मेरो नाम बिशाल हो
```

`--src`/`--tgt` default to `ne`/`en`. The `stub` backend (default `--backend`) just echoes input back &mdash; useful for testing the pipeline without hitting a network or loading a model.

**Subtitles** (single file):

```bash
python -m roman_nepali_ai.cli --srt-in path/to/input.srt --srt-out path/to/output.srt --backend google
python -m roman_nepali_ai.cli --srt-in in.srt --srt-out out.srt --backend google --src en --tgt ne
python -m roman_nepali_ai.cli --srt-in in.srt --srt-out out.srt --backend hf --no-normalize
```

By default, translated subtitles are normalized (long lines wrapped, very short adjacent captions merged). `--no-normalize` disables that.

**Subtitles** (batch, whole folder):

```bash
python -m roman_nepali_ai.cli --batch-in path/to/srt_folder --batch-out path/to/out_folder --backend google
```

## Web demo

`docs/index.html` is a self-contained static page:

```bash
cd docs && python3 -m http.server 8000
# open http://localhost:8000
```

- Transliteration (top card) runs entirely client-side &mdash; no backend needed.
- Translation (bottom card) needs a reachable backend URL (see below); enter it once and it's remembered in your browser (`localStorage`).
- Voice buttons (🎤/🔊) appear automatically where your browser supports the Web Speech API; they're simply hidden otherwise (e.g. Firefox lacks `SpeechRecognition`). Nepali voice quality/availability for text-to-speech varies by OS and browser.

Not yet published via GitHub Pages as of this writing &mdash; run it locally as above, or see [`render.yaml`](render.yaml) / the backend section below for deploying the pieces yourself.

## Backend API

```bash
pip install -e ".[server]"
uvicorn roman_nepali_ai.server:app --reload
```

- `GET /health` &rarr; `{"status": "ok"}`
- `POST /translate` &rarr; `{"text": "...", "backend": "google", "src": "ne", "tgt": "en"}` &rarr; `{"translation": "...", "error": false}`. Errors never produce an HTTP error status &mdash; always `200` with `"error": true` and a message in `"translation"`, so the frontend has one code path to handle.

Deploy config for [Render](https://render.com)'s free tier is in [`render.yaml`](render.yaml) (build: `pip install --upgrade pip && pip install ".[server]"`; start: `uvicorn roman_nepali_ai.server:app --host 0.0.0.0 --port $PORT`). The `google` backend is used in production since it's far lighter than `hf` (no `torch`/model download), at the cost of depending on an unofficial wrapper around Google's translate frontend rather than a stable API.

## Testing

```bash
pip install -e ".[dev,server]"
pytest -q
```

Covers transliteration (formal + casual, including edge cases like anusvara/visarga/dental-vs-retroflex), translation (all three backends, direction plumbing verified via a fake client so it doesn't depend on network), the CLI (argument parsing and all major code paths), and the server (`TestClient`-based, with a fake `Translator` so tests don't need network or a real model). CI (`.github/workflows/ci.yml`) installs `.[dev,server]` and runs the full suite on every push/PR; it deliberately skips the `hf` extra (pulls in `torch`, slow) &mdash; the one test that needs it (`test_hf_rejects_non_ne_en_direction`) skips gracefully via `pytest.importorskip` when `transformers` isn't installed.

## Project layout

```
src/roman_nepali_ai/
  transliterate.py   # roman <-> Devanagari (formal + casual modes)
  translate.py        # Translator class: stub / hf / google backends
  subtitles.py         # SRT parse/write, translate_srt(), normalization
  batch.py               # process_srt_folder() for whole-directory batches
  cli.py                   # argparse CLI wiring all of the above
  server.py                 # FastAPI backend for the web demo's translation panel
docs/                        # static web demo (transliteration.js is a JS port of transliterate.py)
tests/                         # pytest suite, one file per module above
examples/imported_romanized_nepali/   # exploratory notes from early experimentation (not part of the package)
```

## Honest limitations

- **Not a trained model.** Transliteration is rules + a curated dictionary (~65 common words for casual mode); translation is either a no-op stub, a call to Google's translate frontend (via `deep-translator`), or a pretrained Hugging Face model used as-is. Nothing here is trained on this project's own data.
- **Casual-mode dictionary is small.** Words outside it fall back to syllable-by-syllable rules, which don't always match real Nepali orthography (schwa deletion beyond word-final position isn't modeled, some words are genuinely ambiguous &mdash; e.g. `"ma"` could be "I" or the postposition "in/at", and the dictionary can only pick one).
- **`google` backend reliability.** `deep-translator` talks to Google Translate's web frontend, not an official, paid API with an SLA &mdash; it can break or get rate-limited without warning.
- **Voice features depend on the browser.** Web Speech API support (especially `SpeechRecognition`) and Nepali voice availability for text-to-speech vary significantly across browsers and operating systems.
