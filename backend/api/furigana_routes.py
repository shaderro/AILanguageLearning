from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

try:
    from fugashi import Tagger
except ImportError:
    Tagger = None
try:
    from pypinyin import lazy_pinyin, Style
except ImportError:
    lazy_pinyin = None
    Style = None


router = APIRouter(prefix="/api/v2/furigana", tags=["furigana"])


class FuriganaRequest(BaseModel):
    text: str


class FuriganaToken(BaseModel):
    surface: str
    reading: Optional[str] = None
    pos: Optional[str] = None
    needs_ruby: bool


class FuriganaResponse(BaseModel):
    original: str
    ruby_text: str
    tokens: List[FuriganaToken]


class AlignTokenInput(BaseModel):
    token_id: Union[int, str]
    text: str


class FuriganaAlignRequest(BaseModel):
    text: str
    tokens: List[AlignTokenInput]


class FuriganaAlignedToken(BaseModel):
    token_id: Union[int, str]
    reading: Optional[str] = None
    needs_ruby: bool


class FuriganaAlignResponse(BaseModel):
    original: str
    aligned_tokens: List[FuriganaAlignedToken]


_tagger = None


def _katakana_to_hiragana(value: str) -> str:
    chars = []
    for ch in value:
        code = ord(ch)
        if 0x30A1 <= code <= 0x30F6:
            chars.append(chr(code - 0x60))
        else:
            chars.append(ch)
    return "".join(chars)


def _is_kanji(ch: str) -> bool:
    code = ord(ch)
    return 0x4E00 <= code <= 0x9FFF


def _extract_reading(word) -> Optional[str]:
    feature = getattr(word, "feature", None)
    if feature is None:
        return None
    for field_name in ("kana", "pron", "pronBase", "orthBase"):
        value = getattr(feature, field_name, None)
        if value and value != "*":
            return _katakana_to_hiragana(str(value))
    return None


def _build_tagger():
    if Tagger is None:
        raise HTTPException(
            status_code=500,
            detail="fugashi is not installed. Run: python -m pip install \"fugashi[unidic-lite]\"",
        )
    return Tagger()


def _token_reading_for_text(tagger, text: str) -> Optional[str]:
    token_text = (text or "").strip()
    if not token_text:
        return None
    words = list(tagger(token_text))
    if not words:
        return None
    readings: List[str] = []
    for w in words:
        r = _extract_reading(w)
        if r:
            readings.append(r)
    if not readings:
        return None
    return "".join(readings)


def _normalize_kana_text(value: str) -> str:
    return _katakana_to_hiragana(str(value or "")).replace(" ", "").strip()


@router.post("/preview", response_model=FuriganaResponse)
def preview_furigana(payload: FuriganaRequest):
    global _tagger

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")

    if _tagger is None:
        _tagger = _build_tagger()

    result_tokens: List[FuriganaToken] = []
    ruby_parts: List[str] = []

    for word in _tagger(text):
        surface = str(word.surface)
        reading = _extract_reading(word)
        pos = None
        feature = getattr(word, "feature", None)
        if feature is not None:
            pos = getattr(feature, "pos1", None)

        needs_ruby = any(_is_kanji(ch) for ch in surface) and bool(reading)
        result_tokens.append(
            FuriganaToken(
                surface=surface,
                reading=reading,
                pos=pos,
                needs_ruby=needs_ruby,
            )
        )

        if needs_ruby:
            ruby_parts.append(f"<ruby>{surface}<rt>{reading}</rt></ruby>")
        else:
            ruby_parts.append(surface)

    return FuriganaResponse(
        original=text,
        ruby_text="".join(ruby_parts),
        tokens=result_tokens,
    )


@router.post("/align", response_model=FuriganaAlignResponse)
def align_furigana_tokens(payload: FuriganaAlignRequest):
    global _tagger

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")

    if _tagger is None:
        _tagger = _build_tagger()

    aligned_tokens: List[FuriganaAlignedToken] = []
    for token in payload.tokens or []:
        surface = token.text or ""
        reading = _token_reading_for_text(_tagger, surface)
        normalized_surface = _normalize_kana_text(surface)
        normalized_reading = _normalize_kana_text(reading or "")
        # Prefer showing ruby when token includes kanji, or reading differs from visible token text.
        needs_ruby = bool(reading) and (
            any(_is_kanji(ch) for ch in surface) or
            (normalized_reading != "" and normalized_reading != normalized_surface)
        )
        aligned_tokens.append(
            FuriganaAlignedToken(
                token_id=token.token_id,
                reading=reading,
                needs_ruby=needs_ruby,
            )
        )

    return FuriganaAlignResponse(
        original=text,
        aligned_tokens=aligned_tokens,
    )


@router.post("/zh-preview", response_model=FuriganaResponse)
def preview_chinese_pinyin(payload: FuriganaRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")
    if lazy_pinyin is None or Style is None:
        raise HTTPException(
            status_code=500,
            detail='pypinyin is not installed. Run: python -m pip install pypinyin',
        )

    result_tokens: List[FuriganaToken] = []
    ruby_parts: List[str] = []

    for ch in text:
        if ch.isspace():
            result_tokens.append(FuriganaToken(surface=ch, reading=None, pos=None, needs_ruby=False))
            ruby_parts.append(ch)
            continue

        reading_list = lazy_pinyin(ch, style=Style.TONE)
        reading = reading_list[0] if reading_list else None
        is_hanzi = bool("\u4e00" <= ch <= "\u9fff")
        needs_ruby = is_hanzi and bool(reading)

        result_tokens.append(
            FuriganaToken(
                surface=ch,
                reading=reading,
                pos=None,
                needs_ruby=needs_ruby,
            )
        )
        if needs_ruby:
            ruby_parts.append(f"<ruby>{ch}<rt>{reading}</rt></ruby>")
        else:
            ruby_parts.append(ch)

    return FuriganaResponse(
        original=text,
        ruby_text="".join(ruby_parts),
        tokens=result_tokens,
    )


@router.post("/zh-align", response_model=FuriganaAlignResponse)
def align_chinese_pinyin_tokens(payload: FuriganaAlignRequest):
    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text cannot be empty")
    if lazy_pinyin is None or Style is None:
        raise HTTPException(
            status_code=500,
            detail='pypinyin is not installed. Run: python -m pip install pypinyin',
        )

    aligned_tokens: List[FuriganaAlignedToken] = []
    for token in payload.tokens or []:
        surface = token.text or ""
        parts = lazy_pinyin(surface, style=Style.TONE)
        reading = " ".join([p for p in parts if p]).strip() or None
        needs_ruby = any("\u4e00" <= ch <= "\u9fff" for ch in surface) and bool(reading)
        aligned_tokens.append(
            FuriganaAlignedToken(
                token_id=token.token_id,
                reading=reading,
                needs_ruby=needs_ruby,
            )
        )

    return FuriganaAlignResponse(
        original=text,
        aligned_tokens=aligned_tokens,
    )
