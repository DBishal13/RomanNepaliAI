"""CLI for RomanNepaliAI: Nepali->English translation (supports stub, Hugging Face, and SRT pipeline)."""

import argparse
from .translate import Translator
from .subtitles import translate_srt

def main():
    parser = argparse.ArgumentParser(description="RomanNepaliAI translation CLI")
    parser.add_argument("text", nargs='?', help="Text to translate (Nepali). Omit when using --srt")
    parser.add_argument("--backend", choices=["stub", "hf", "google"], default="stub", help="Backend to use")
    parser.add_argument("--model", help="Model name for HF backend (e.g., Helsinki-NLP/opus-mt-ne-en)")
    parser.add_argument("--srt-in", help="Path to input SRT to translate")
    parser.add_argument("--srt-out", help="Path to output translated SRT (required if --srt-in is given)")
    parser.add_argument("--batch-in", help="Directory containing SRTs to batch-translate")
    parser.add_argument("--batch-out", help="Destination directory for translated SRTs (required if --batch-in is given)")
    parser.add_argument("--no-normalize", action="store_true", help="Disable post-translation subtitle normalization (wrapping/merging)")
    args = parser.parse_args()

    if args.srt_in:
        if not args.srt_out:
            print("--srt-out is required when --srt-in is provided")
            return
        try:
            translate_srt(args.srt_in, args.srt_out, backend=args.backend, model_name=args.model, normalize=(not args.no_normalize))
            print(f"Wrote translated SRT to {args.srt_out}")
        except Exception as e:
            print(f"[srt translation error] {e}")
        return

    if args.batch_in:
        if not args.batch_out:
            print("--batch-out is required when --batch-in is provided")
            return
        try:
            from .batch import process_srt_folder
            count = process_srt_folder(args.batch_in, args.batch_out, backend=args.backend, model_name=args.model)
            print(f"Processed {count} files from {args.batch_in} -> {args.batch_out}")
        except Exception as e:
            print(f"[batch translation error] {e}")
        return

    if not args.text:
        print("Either provide text to translate or use --srt-in for subtitles")
        return

    translator = Translator(backend=args.backend, model_name=args.model)
    try:
        out = translator.translate(args.text)
    except Exception as e:
        print(f"[translation error] {e}")
        out = args.text
    print(out)


if __name__ == "__main__":
    main()
