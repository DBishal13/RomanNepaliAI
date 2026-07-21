"""Simple CLI for RomanNepaliAI transliteration stubs."""

import argparse
from .transliterate import roman_to_devanagari, devanagari_to_roman


def main():
    parser = argparse.ArgumentParser(description="RomanNepaliAI transliteration CLI")
    parser.add_argument("text", help="Text to transliterate")
    parser.add_argument("--reverse", action="store_true", help="Transliterate Devanagari to Roman")
    args = parser.parse_args()

    if args.reverse:
        print(devanagari_to_roman(args.text))
    else:
        print(roman_to_devanagari(args.text))


if __name__ == "__main__":
    main()
