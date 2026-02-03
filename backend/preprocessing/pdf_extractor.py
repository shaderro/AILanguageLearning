#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PDF 正文提取模块

输入 PDF 二进制内容，输出尽可能干净的纯文本正文。
优先使用纯 Python 依赖 pypdf，便于部署（无额外系统库需求）。
"""

from __future__ import annotations

import io
import re


def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        return ""

    try:
        # pypdf: https://pypdf.readthedocs.io/
        from pypdf import PdfReader  # type: ignore
    except ImportError:
        print("[ERROR] [PDF Extractor] pypdf 未安装，无法提取 PDF 正文")
        return ""

    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
    except Exception as e:
        print(f"[ERROR] [PDF Extractor] 解析 PDF 失败: {e}")
        return ""

    # 尝试解密（部分 PDF 会被标记为 encrypted，但实际可用空密码打开）
    try:
        if getattr(reader, "is_encrypted", False):
            try:
                reader.decrypt("")  # type: ignore[attr-defined]
            except Exception:
                # 解密失败就继续尝试提取，提取失败时会返回空
                pass
    except Exception:
        pass

    chunks: list[str] = []
    for idx, page in enumerate(getattr(reader, "pages", []) or []):
        try:
            text = page.extract_text() or ""
        except Exception as e:
            print(f"[WARN] [PDF Extractor] 第 {idx + 1} 页提取失败: {e}")
            text = ""
        if text:
            chunks.append(text)

    raw_text = "\n".join(chunks)
    cleaned = _clean_extracted_text(raw_text)

    if cleaned:
        print(f"[OK] [PDF Extractor] 提取成功，正文长度: {len(cleaned)} 字符")
    else:
        print("[WARN] [PDF Extractor] 提取结果为空（可能是扫描版/图片PDF）")

    return cleaned


def _clean_extracted_text(text: str) -> str:
    if not text:
        return ""

    # 统一换行
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 去掉多余空格（但保留段落结构）
    lines = [ln.strip() for ln in text.split("\n")]
    lines = [ln for ln in lines if ln]  # 去空行
    text = "\n".join(lines)

    # 合并过多换行
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 常见连字符断行修复： "hyphen-\nated" -> "hyphenated"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    return text.strip()

