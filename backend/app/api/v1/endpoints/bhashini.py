from fastapi import APIRouter
from pydantic import BaseModel
from app.services.bhashini_service import BhashiniTranslationService

router = APIRouter()

class TranslationRequest(BaseModel):
    text: str
    source_lang: str = "en"
    target_lang: str = "hi"

@router.post("/bhashini/translate")
async def translate_text(request: TranslationRequest):
    """
    Bhashini NMT Translation Endpoint for 22 scheduled Indian languages.
    """
    return await BhashiniTranslationService.translate_text(
        text=request.text,
        source_lang=request.source_lang,
        target_lang=request.target_lang
    )
