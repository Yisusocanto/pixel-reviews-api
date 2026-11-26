import io
import wave

from src.services.gemini.client import pcm_to_wav_bytes


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
