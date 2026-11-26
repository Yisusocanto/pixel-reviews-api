import base64
import io
import json
import logging
import wave
from typing import Any

import httpx
from fastapi import HTTPException, status

from src.core.settings import settings

logger = logging.getLogger("gemini_service")

RETRYABLE_STATUS_CODES = {404, 429, 503}

TEXT_MODEL_FALLBACKS = (
    "gemini-3-flash-preview",
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
)

TTS_MODEL_FALLBACKS = (
    "gemini-3.8-flash-tts",
    "gemini-2.5-flash-preview-tts",
    "gemini-3.1-flash-tts-preview",
)


def _build_candidate_models(primary: str, fallbacks: tuple[str, ...]) -> list[str]:
    ordered: list[str] = []
    for candidate in (primary, *fallbacks):
        cleaned = candidate.strip()
        if cleaned and cleaned not in ordered:
            ordered.append(cleaned)
    return ordered


def pcm_to_wav_bytes(
    pcm_data: bytes,
    sample_rate: int = 24000,
    channels: int = 1,
    bit_depth: int = 16,
) -> bytes:
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(bit_depth // 8)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(pcm_data)
    return wav_io.getvalue()


class GeminiService:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        creative_model: str,
        tts_model: str,
        default_voice: str,
        translation_model: str,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.creative_model = creative_model
        self.tts_model = tts_model
        self.default_voice = default_voice
        self.translation_model = translation_model

    def _ensure_configured(self) -> None:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="GEMINI_API_KEY is not configured on the server",
            )

    async def _post_with_fallback(
        self,
        models: list[str],
        payload: dict[str, Any],
        timeout: float,
    ) -> tuple[dict[str, Any], str]:
        last_status = 502
        last_body = ""
        async with httpx.AsyncClient(timeout=timeout) as client:
            for model_name in models:
                endpoint = f"{self.base_url}/models/{model_name}:generateContent"
                try:
                    response = await client.post(
                        endpoint,
                        params={"key": self.api_key},
                        json=payload,
                    )
                except httpx.TimeoutException:
                    last_status = 504
                    last_body = f"Timeout calling {model_name}"
                    logger.warning(
                        "[GEMINI] Model %s timed out after %.1fs; trying fallback",
                        model_name,
                        timeout,
                    )
                    continue
                except httpx.HTTPError as exc:
                    last_status = 502
                    last_body = str(exc)[:400]
                    logger.warning(
                        "[GEMINI] Network error on %s (%s); trying fallback",
                        model_name,
                        exc,
                    )
                    continue

                if response.status_code < 400:
                    return response.json(), model_name

                last_status = response.status_code
                last_body = response.text[:400]
                if response.status_code in RETRYABLE_STATUS_CODES:
                    logger.warning(
                        "[GEMINI] Model %s returned %s; trying fallback",
                        model_name,
                        response.status_code,
                    )
                    continue

                logger.error(
                    "[GEMINI] Request failed on %s (%s): %s",
                    model_name,
                    response.status_code,
                    last_body,
                )
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Gemini API error ({response.status_code})",
                )

        logger.error(
            "[GEMINI] All candidate models failed (last=%s): %s",
            last_status,
            last_body,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Gemini API error ({last_status})",
        )

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.8,
    ) -> dict[str, Any]:
        self._ensure_configured()
        models = _build_candidate_models(model or self.creative_model, TEXT_MODEL_FALLBACKS)

        payload: dict[str, Any] = {
            "systemInstruction": {
                "parts": [{"text": system_instruction}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "responseMimeType": "application/json",
                "responseSchema": response_schema,
            },
        }

        body, used_model = await self._post_with_fallback(models, payload, timeout=35.0)
        logger.info("[GEMINI] Generated structured JSON via %s", used_model)
        try:
            text_output = body["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_output)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.exception("[GEMINI] Invalid structured JSON response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid structured response from Gemini",
            ) from exc

    async def generate_studio_tts(
        self,
        narration_text: str,
        voice_direction: str,
        voice_name: str | None = None,
    ) -> tuple[bytes, float]:
        self._ensure_configured()
        selected_voice = voice_name or self.default_voice
        models = _build_candidate_models(self.tts_model, TTS_MODEL_FALLBACKS)

        directed_prompt = (
            f"Voice direction: {voice_direction.strip()}\n\n"
            f"Transcript to read aloud:\n{narration_text.strip()}"
        )

        payload: dict[str, Any] = {
            "contents": [
                {
                    "parts": [{"text": directed_prompt}],
                }
            ],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": selected_voice,
                        }
                    }
                },
            },
        }

        body, used_model = await self._post_with_fallback(models, payload, timeout=90.0)
        self.tts_model = used_model
        logger.info("[GEMINI] Synthesized studio TTS via %s (%s)", used_model, selected_voice)
        try:
            inline_data = body["candidates"][0]["content"]["parts"][0]["inlineData"]
            pcm_bytes = base64.b64decode(inline_data["data"])
        except (KeyError, IndexError, ValueError) as exc:
            logger.exception("[GEMINI] Missing inlineData audio in TTS response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid audio payload from Gemini TTS",
            ) from exc

        wav_bytes = pcm_to_wav_bytes(pcm_bytes, sample_rate=24000, channels=1, bit_depth=16)
        duration_seconds = round(len(pcm_bytes) / (24000 * 2), 2)
        return wav_bytes, duration_seconds

    async def translate_game_copy_to_spanish(
        self,
        title: str,
        description: str,
        storyline: str | None = None,
    ) -> dict[str, str | None]:
        if not self.api_key or (not description.strip() and not (storyline or "").strip()):
            return {"description_es": None, "storyline_es": None}

        schema: dict[str, Any] = {
            "type": "OBJECT",
            "properties": {
                "description_es": {"type": "STRING"},
                "storyline_es": {"type": "STRING", "nullable": True},
            },
            "required": ["description_es"],
        }

        system_prompt = (
            "Eres un editor experto en videojuegos en español neutro internacional. "
            "Traduce descripciones y sinopsis manteniendo los nombres propios oficiales "
            "de franquicias, personajes y mecánicas gamer habituales sin sonar literal."
        )
        user_prompt = (
            f"Juego: {title}\n\n"
            f"Description (EN):\n{description}\n\n"
            f"Storyline (EN):\n{storyline or ''}"
        )

        result = await self.generate_structured_json(
            prompt=user_prompt,
            system_instruction=system_prompt,
            response_schema=schema,
            model=self.translation_model,
            temperature=0.25,
        )
        return {
            "description_es": result.get("description_es") or None,
            "storyline_es": result.get("storyline_es") or None,
        }


def build_default_gemini_service() -> GeminiService:
    return GeminiService(
        api_key=settings.GEMINI_API_KEY,
        base_url=settings.GEMINI_API_URL,
        creative_model=settings.GEMINI_CREATIVE_MODEL,
        tts_model=settings.GEMINI_TTS_MODEL,
        default_voice=settings.GEMINI_TTS_VOICE,
        translation_model=settings.GEMINI_TRANSLATION_MODEL,
    )
