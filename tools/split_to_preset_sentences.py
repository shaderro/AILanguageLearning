#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
将原始整篇文本（不分句）转换成预置文章 JSON 里的 "sentences": [ ... ] 段。

用法示例（在项目根目录运行）：

    # 从文件读取，语言中文
    python tools/split_to_preset_sentences.py zh < raw_article.txt

    # 从文件读取，语言英文
    python tools/split_to_preset_sentences.py en < raw_article_en.txt

    # 默认语言 zh（参数可省略）
    python tools/split_to_preset_sentences.py < raw_zh.txt
"""

import os
import sys

# 确保可以 import 项目内模块
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.preprocessing.sentence_processor import split_sentences  # type: ignore
from backend.preprocessing.language_classification import get_language_code  # type: ignore


def main() -> None:
    # 语言参数：zh/en/de 或 "中文"/"英文"/"德文"
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("-"):
        lang_arg = sys.argv[1]
    else:
        lang_arg = "zh"  # 默认按中文处理

    language_code = get_language_code(lang_arg)
    if not language_code:
        print(f"[WARN] 无法识别语言参数 {lang_arg!r}，将按中文处理 (zh)", file=sys.stderr)
        language_code = "zh"

    # 从 stdin 读取整篇原始文本
    raw_text = sys.stdin.read()
    if not raw_text.strip():
        print("[ERROR] 未从标准输入读取到任何文本。请用重定向或管道传入原文。", file=sys.stderr)
        sys.exit(1)

    # 使用项目内的分句逻辑
    sentences = split_sentences(raw_text, language_code=language_code)

    # 输出 JSON 片段，方便直接粘贴到预置 JSON 中
    print('  "sentences": [')
    for i, s in enumerate(sentences):
        s_clean = s.strip().replace('"', '\\"')
        comma = "," if i < len(sentences) - 1 else ""
        print(f'    "{s_clean}"{comma}')
    print("  ]")


if __name__ == "__main__":
    main()

