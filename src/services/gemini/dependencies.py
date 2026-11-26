from typing import Annotated

from fastapi import Depends

from src.services.gemini.client import GeminiService, build_default_gemini_service


def get_gemini_service() -> GeminiService:
    return build_default_gemini_service()


GeminiServiceDep = Annotated[GeminiService, Depends(get_gemini_service)]
