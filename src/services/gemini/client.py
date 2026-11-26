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

    async def generate_structured_json(
        self,
        prompt: str,
        system_instruction: str,
        response_schema: dict[str, Any],
        model: str | None = None,
        temperature: float = 0.8,
    ) -> dict[str, Any]:
        self._ensure_configured()
        target_model = model or self.creative_model
        endpoint = f"{self.base_url}/models/{target_model}:generateContent"

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

        async with httpx.AsyncClient(timeout=75.0) as client:
            response = await client.post(
                endpoint,
                params={"key": self.api_key},
                json=payload,
            )

        if response.status_code >= 400:
            logger.error(
                "[GEMINI] Structured generation failed (%s): %s",
                response.status_code,
                response.text[:400],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini API error ({response.status_code})",
            )

        body = response.json()
        try:
            text_output = body["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_output)
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            logger.exception("[GEMINI] Invalid structured JSON response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid structured response from Gemini Pro",
            ) from exc

    async def generate_studio_tts(
        self,
        narration_text: str,
        voice_direction: str,
        voice_name: str | None = None,
    ) -> tuple[bytes, float]:
        self._ensure_configured()
        selected_voice = voice_name or self.default_voice
        endpoint = f"{self.base_url}/models/{self.tts_model}:generateContent"

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

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                endpoint,
                params={"key": self.api_key},
                json=payload,
            )

        if response.status_code >= 400:
            logger.error(
                "[GEMINI] TTS generation failed (%s): %s",
                response.status_code,
                response.text[:400],
            )
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Gemini TTS error ({response.status_code})",
            )

        body = response.json()
        try:
            inline_data = body["candidates"][0]["content"]["parts"][0]["inlineData"]
            pcm_bytes = base64.b64decode(inline_data["data"])
        except (KeyError, IndexError, ValueError) as exc:
            logger.exception("[GEMINI] Missing inlineData audio in TTS response")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid audio payload from Gemini Pro TTS",
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
