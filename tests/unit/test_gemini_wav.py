import io
import wave

from src.services.gemini.client import (
    TEXT_MODEL_FALLBACKS,
    TRANSLATION_MODEL_FALLBACKS,
    TTS_MODEL_FALLBACKS,
    _build_candidate_models,
    pcm_to_wav_bytes,
)


def test_pcm_to_wav_bytes_wraps_24khz_mono_16bit_header() -> None:
    raw_pcm = b"\x01\x02" * 12000
    wav_data = pcm_to_wav_bytes(raw_pcm, sample_rate=24000, channels=1, bit_depth=16)

    assert wav_data[:4] == b"RIFF"
    assert wav_data[8:12] == b"WAVE"

    with wave.open(io.BytesIO(wav_data), "rb") as reader:
        assert reader.getnchannels() == 1
        assert reader.getsampwidth() == 2
        assert reader.getframerate() == 24000
        assert reader.getnframes() == 12000


def test_build_candidate_models_deduplicates_and_keeps_fast_fallbacks() -> None:
    text_models = _build_candidate_models("gemini-3.1-flash-lite-preview", TEXT_MODEL_FALLBACKS)
    assert text_models[0] == "gemini-3.1-flash-lite-preview"
    assert "gemini-3.1-flash-lite" in text_models
    assert "gemini-3.6-flash" in text_models
    assert len(text_models) == len(set(text_models))

    translation_models = _build_candidate_models(
        "gemini-3.1-flash-lite-preview", TRANSLATION_MODEL_FALLBACKS
    )
    assert "gemini-3-flash-preview" not in translation_models
    assert "gemini-3.8-flash" not in translation_models

    tts_models = _build_candidate_models("gemini-3.8-flash-tts", TTS_MODEL_FALLBACKS)
    assert tts_models[0] == "gemini-3.8-flash-tts"
    assert "gemini-3.8-flash-lite-tts" in tts_models
    assert len(tts_models) == len(set(tts_models))
