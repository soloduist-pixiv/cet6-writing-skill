#!/usr/bin/env python3
"""Transparent practice checks; not an official CET counter or scoring system."""
import argparse
import json
import re
import sys
from pathlib import Path


def normalize(text):
    # Ignore typography and layout, preserve wording, case, and punctuation.
    text = text.translate(str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'}))
    return " ".join(text.split())


def check(text, opening=None, minimum=150, maximum=200):
    # Count English/numeric tokens. Internal apostrophes and hyphens stay in a token.
    normalized = normalize(text)
    tokens = re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", normalized)
    split_hyphens = sum(len(token.split("-")) for token in tokens)
    result = {
        "words": len(tokens),
        "words_if_hyphens_split": split_hyphens,
        "minimum": minimum,
        "maximum": maximum,
        "length_ok": minimum <= len(tokens) <= maximum,
        "length_ok_if_hyphens_split": minimum <= split_hyphens <= maximum,
        "opening_ok": None,
        "opening_status": "not_checked",
        "non_english_text_present": bool(re.search(r"[^\x00-\x7f\u2010-\u2027]", text)),
        "scope": "Body only, including supplied opening; title and notes must be excluded by caller.",
        "notice": "Practice count only. Does not assess topic coverage, grammar, or official scoring.",
    }
    if opening is not None:
        expected = normalize(opening)
        # Reject trivial prefix matches such as 'Learn' matching 'Learning'.
        matches = normalized.startswith(expected) and (
            len(normalized) == len(expected)
            or not expected[-1:].isalnum()
            or not normalized[len(expected):len(expected) + 1].isalnum()
        )
        result["opening_ok"] = bool(expected) and matches
        result["opening_status"] = "match" if result["opening_ok"] else "mismatch"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("essay", type=Path, help="UTF-8 plain text containing the essay body only")
    parser.add_argument("--opening-file", type=Path, help="UTF-8 text of exact required opening, without outer quote delimiters")
    parser.add_argument("--min", type=int, default=150, dest="minimum")
    parser.add_argument("--max", type=int, default=200, dest="maximum")
    args = parser.parse_args()
    if args.minimum < 0 or args.maximum < args.minimum:
        parser.error("Require 0 <= min <= max")
    try:
        text = args.essay.read_text(encoding="utf-8-sig")
        opening = args.opening_file.read_text(encoding="utf-8-sig") if args.opening_file else None
    except (OSError, UnicodeError) as exc:
        parser.exit(2, f"Cannot read input: {exc}\n")
    result = check(text, opening, args.minimum, args.maximum)
    # ASCII JSON remains readable on terminals using legacy Windows encodings.
    print(json.dumps(result, ensure_ascii=True, indent=2))
    sys.exit(0 if result["length_ok"] and result["opening_ok"] is not False else 1)


if __name__ == "__main__":
    main()
