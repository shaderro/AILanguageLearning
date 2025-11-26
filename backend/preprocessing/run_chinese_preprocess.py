#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utility script to run EnhancedArticleProcessor on a Chinese text file
and print the resulting data structure (sentences / tokens / word_tokens /
vocab_expressions).
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Ensure backend package imports work when running from project root
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.preprocessing.enhanced_processor import EnhancedArticleProcessor  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run EnhancedArticleProcessor on a Chinese article and print the result."
    )
    parser.add_argument(
        "--file",
        required=True,
        help="Path to the text file that contains the article.",
    )
    parser.add_argument(
        "--title",
        default="Uploaded Article",
        help="Optional article title.",
    )
    parser.add_argument(
        "--text-id",
        type=int,
        default=1,
        help="Optional text ID (defaults to 1).",
    )
    parser.add_argument(
        "--language",
        default="zh",
        help="Language code to pass into the processor (default: zh).",
    )
    parser.add_argument(
        "--enable-difficulty",
        action="store_true",
        help="Enable difficulty estimation (disabled by default for faster testing).",
    )
    parser.add_argument(
        "--enable-vocab",
        action="store_true",
        help="Enable vocab explanation generation (disabled by default).",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    text_path = Path(args.file).expanduser()

    if not text_path.exists():
        print(f"❌ File not found: {text_path}")
        sys.exit(1)

    article_text = text_path.read_text(encoding="utf-8")

    processor = EnhancedArticleProcessor()
    processor.enable_advanced_features(
        enable_difficulty=args.enable_difficulty,
        enable_vocab=args.enable_vocab,
    )

    result = processor.process_article_enhanced(
        article_text,
        text_id=args.text_id,
        text_title=args.title,
        language=args.language,
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

