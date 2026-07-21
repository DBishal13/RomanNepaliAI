"""CLI for RomanNepaliAI: Nepali->English translation (supports stub and Hugging Face backends)."""

import argparse
from .translate import Translator

ndef main():
    parser = argparse.ArgumentParser(description="RomanNepaliAI translation CLI")
    parser.add_argument("text", help="Text to translate (Nepali)")
    parser.add_argument("--backend", choices=["stub", "hf"], default="stub", help="Backend to use")
    parser.add_argument("--model", help="Model name for HF backend (e.g., Helsinki-NLP/opus-mt-ne-en)")
    args = parser.parse_args()

    translator = Translator(backend=args.backend, model_name=args.model)
    try:
        out = translator.translate(args.text)
    except Exception as e:
        print(f"[translation error] {e}")
        out = args.text
    print(out)


if __name__ == "__main__":
    main()
