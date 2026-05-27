"""Server-side quick translation (Google GTX / Lingva / fallbacks)."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Awaitable, Callable, List, Optional, Tuple
from urllib.parse import quote

import httpx

logger = logging.getLogger(__name__)

ProviderFn = Callable[[str, str, str], Awaitable[Optional[str]]]

LANG_NAME_TO_CODE = {
    "中文": "zh",
    "英文": "en",
    "英语": "en",
    "德文": "de",
    "德语": "de",
    "西班牙语": "es",
    "法语": "fr",
    "日语": "ja",
    "日文": "ja",
    "韩语": "ko",
    "阿拉伯语": "ar",
    "俄语": "ru",
    "chinese": "zh",
    "english": "en",
    "german": "de",
    "spanish": "es",
    "french": "fr",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
    "russian": "ru",
}

SUPPORTED = frozenset({"de", "en", "zh", "ja", "fr", "es", "it", "pt", "ru", "ar", "ko"})

_MYMEMORY_QUOTA_RE = re.compile(
    r"MYMEMORY\s+WARNING|NEXT\s+AVAILABLE\s+IN|USAGELIMITS",
    re.IGNORECASE,
)

_GTX_TL_MAP = {
    "zh": "zh-CN",
    "en": "en",
    "de": "de",
    "ja": "ja",
    "fr": "fr",
    "es": "es",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "ar": "ar",
    "ko": "ko",
}


def normalize_lang_code(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if s in LANG_NAME_TO_CODE:
        return LANG_NAME_TO_CODE[s]
    lower = s.lower().replace("_", "-")
    if lower in LANG_NAME_TO_CODE:
        return LANG_NAME_TO_CODE[lower]
    code = lower.split("-")[0]
    if len(code) == 2 and code.isalpha():
        return code
    return None


def _sanitize(text: str) -> str:
    if not text:
        return ""
    s = str(text).replace("\r", "").strip()
    if _MYMEMORY_QUOTA_RE.search(s):
        return ""
    return s


def _truncate_for_api(text: str, max_len: int = 500) -> str:
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    for sep in (".", "?", "!", "。"):
        idx = truncated.rfind(sep)
        if idx > max_len * 0.6:
            return truncated[: idx + 1]
    sp = truncated.rfind(" ")
    if sp > max_len * 0.6:
        return truncated[:sp] + "..."
    return truncated + "..."


async def _google_gtx(text: str, source: str, target: str) -> Optional[str]:
    """Unofficial Google Translate client=gtx (usually fast; no API key)."""
    tl = _GTX_TL_MAP.get(target, target)
    sl = source if source in SUPPORTED else "auto"
    q = quote(_truncate_for_api(text, 1200))
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={sl}&tl={tl}&dt=t&q={q}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
        if not data or not isinstance(data[0], list):
            return None
        out = "".join(part[0] for part in data[0] if part and part[0])
        out = _sanitize(out)
        if out and out.lower() != text.strip().lower():
            return out
    except Exception as exc:
        logger.warning("Google GTX translate failed: %s", exc)
    return None


async def _mymemory(text: str, source: str, target: str) -> Optional[str]:
    q = quote(_truncate_for_api(text))
    url = f"https://api.mymemory.translated.net/get?q={q}&langpair={source}|{target}"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as exc:
        logger.warning("MyMemory request failed: %s", exc)
        return None

    if data.get("responseStatus") != 200:
        return None

    candidates = []
    rd = data.get("responseData") or {}
    if rd.get("translatedText"):
        candidates.append(_sanitize(rd["translatedText"]))

    for m in data.get("matches") or []:
        if m and m.get("translation"):
            candidates.append(_sanitize(m["translation"]))

    original_lower = text.strip().lower()
    for c in candidates:
        if c and c.lower() != original_lower:
            return c
    return None


async def _libre(text: str, source: str, target: str) -> Optional[str]:
    if source not in SUPPORTED or target not in SUPPORTED:
        return None
    payload = {"q": text, "source": source, "target": target, "format": "text"}
    for base in ("https://libretranslate.com",):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.post(f"{base}/translate", json=payload)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                out = _sanitize((data or {}).get("translatedText") or "")
                if out and out.lower() != text.strip().lower():
                    return out
        except Exception as exc:
            logger.warning("LibreTranslate %s failed: %s", base, exc)
    return None


async def _lingva(text: str, source: str, target: str) -> Optional[str]:
    if source not in SUPPORTED or target not in SUPPORTED:
        return None
    q = quote(_truncate_for_api(text, 400))
    url = f"https://lingva.ml/api/v1/{source}/{target}/{q}"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            out = _sanitize((data or {}).get("translation") or "")
            if out and out.lower() != text.strip().lower():
                return out
    except Exception as exc:
        logger.warning("Lingva request failed: %s", exc)
    return None


_LANG_LABEL = {
    "de": "German",
    "en": "English",
    "zh": "Simplified Chinese",
    "ja": "Japanese",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ar": "Arabic",
    "ko": "Korean",
}


async def _deepseek(text: str, source: str, target: str) -> Optional[str]:
    if os.getenv("QUICK_TRANSLATE_USE_LLM", "").strip().lower() not in ("1", "true", "yes"):
        return None
    try:
        from backend.config import OPENAI_API_KEY
    except ImportError:
        return None
    if not OPENAI_API_KEY:
        return None

    src_label = _LANG_LABEL.get(source, source)
    tgt_label = _LANG_LABEL.get(target, target)

    def _call() -> str:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Translate the user's text. Output only the translation with no quotes or explanation.",
                },
                {
                    "role": "user",
                    "content": f"Translate from {src_label} to {tgt_label}:\n\n{text}",
                },
            ],
            max_tokens=800,
            temperature=0.1,
        )
        return (resp.choices[0].message.content or "").strip()

    try:
        result = await asyncio.wait_for(asyncio.to_thread(_call), timeout=20.0)
        out = _sanitize(result)
        if out and out.lower() != text.strip().lower():
            return out
    except Exception as exc:
        logger.warning("DeepSeek translate failed: %s", exc)
    return None


async def _first_success(
    text: str,
    source: str,
    target: str,
    providers: List[ProviderFn],
    timeout: float = 10.0,
) -> Optional[str]:
    """Run providers in parallel; return the first non-empty result."""

    async def _run(provider: ProviderFn) -> Optional[str]:
        try:
            return await provider(text, source, target)
        except Exception as exc:
            logger.warning("%s failed: %s", getattr(provider, "__name__", "provider"), exc)
            return None

    tasks = [asyncio.create_task(_run(p)) for p in providers]
    try:
        for finished in asyncio.as_completed(tasks, timeout=timeout):
            try:
                result = await finished
            except Exception:
                continue
            if result:
                return result
    except asyncio.TimeoutError:
        logger.warning("Translation race timed out after %.1fs", timeout)
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
    return None


async def translate_text(text: str, source_lang: str, target_lang: str) -> Optional[str]:
    """Translate text; returns None if all providers fail."""
    cleaned = (text or "").strip()
    if not cleaned:
        raise ValueError("empty_text")

    source = normalize_lang_code(source_lang)
    target = normalize_lang_code(target_lang)
    if not source or not target:
        raise ValueError("unsupported_language")
    if source == target:
        return None

    # Fast path: Google GTX + Lingva in parallel (avoids 30s+ sequential free-API chain)
    fast = await _first_success(
        cleaned,
        source,
        target,
        [_google_gtx, _lingva],
        timeout=10.0,
    )
    if fast:
        return fast

    for provider in (_mymemory, _libre, _deepseek):
        result = await provider(cleaned, source, target)
        if result:
            return result
    return None
