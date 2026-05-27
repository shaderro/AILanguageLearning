"""Quick translation API (proxy for hover / sentence translation)."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v2/translate", tags=["translate"])


class QuickTranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)
    source_lang: str = Field(..., min_length=2, max_length=20)
    target_lang: str = Field(..., min_length=2, max_length=20)


@router.post("/quick")
async def quick_translate(body: QuickTranslateRequest):
    from backend.services.quick_translate import translate_text

    try:
        translation = await translate_text(body.text, body.source_lang, body.target_lang)
    except ValueError as exc:
        code = str(exc)
        if code == "empty_text":
            raise HTTPException(status_code=400, detail="文本不能为空")
        if code == "unsupported_language":
            raise HTTPException(status_code=400, detail="不支持的语言")
        raise HTTPException(status_code=400, detail=code)

    return {
        "success": True,
        "data": {
            "translation": translation,
            "source_lang": body.source_lang,
            "target_lang": body.target_lang,
        },
    }
