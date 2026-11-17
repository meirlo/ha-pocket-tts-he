import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .settings import Settings

MODEL_REPO = "thewh1teagle/pocket-tts-onnx"
MODEL_REVISION = "110f5251188e9407b4f724acdd8b0dfd0b20692a"
MODEL_FILENAME = "pocket-tts-english-ipa.onnx"
RENIKUD_REPO = "renikud/renikud"
RENIKUD_REVISION = "a59c632c8cbac0f8c63f298cad77ef3a3a2547c9"
RENIKUD_FILENAME = "model.onnx"
_LOGGER = logging.getLogger(__name__)


class Engine(Protocol):
    @property
    def sample_rate(self) -> int: ...

    def voices(self) -> list[str]: ...

    def voice_language(self, voice: str) -> str: ...

    def stream(self, text: str, voice: str) -> Iterator[NDArray[np.float32]]: ...


class NativeEngine(Protocol):
    @property
    def sample_rate(self) -> int: ...

    def voices(self) -> list[str]: ...

    def stream(
        self, text: str, voice: str, phonemes: bool = False, decode_steps: int | None = None
    ) -> Iterator[NDArray[np.float32]]: ...


class PocketEngine:
    def __init__(
        self, model: NativeEngine, languages: dict[str, str], renikud_path: Path | None
    ) -> None:
        self.model = model
        self.languages = languages
        self.renikud_path = renikud_path

    @property
    def sample_rate(self) -> int:
        return self.model.sample_rate

    def voices(self) -> list[str]:
        return self.model.voices()

    def voice_language(self, voice: str) -> str:
        return self.languages[voice]

    def stream(self, text: str, voice: str) -> Iterator[NDArray[np.float32]]:
        if self.voice_language(voice) == "he":
            from pocket_tts_onnx import phonemize_mixed

            if self.renikud_path is None:
                raise RuntimeError("Hebrew synthesis requires a Renikud model")
            # The generator body runs on the inference worker, including G2P.
            text = phonemize_mixed(text, model=self.renikud_path)
            if not text.strip():
                raise ValueError("Hebrew preprocessing generated no speakable text")
            yield from self.model.stream(text, voice=voice, phonemes=True, decode_steps=2)
        else:
            yield from self.model.stream(text, voice=voice)


def load_engine(settings: Settings, data_dir: Path) -> Engine:
    from huggingface_hub import hf_hub_download
    from pocket_tts_onnx import PocketTTS

    if settings.model_path:
        path = Path(settings.model_path)
        if not path.is_file():
            raise FileNotFoundError(f"Model does not exist: {path}")
    else:
        _LOGGER.info(
            "Loading %s at revision %s (cached after first download)",
            MODEL_FILENAME,
            MODEL_REVISION,
        )
        path = Path(
            hf_hub_download(
                repo_id=MODEL_REPO,
                filename=MODEL_FILENAME,
                revision=MODEL_REVISION,
                cache_dir=data_dir / "huggingface",
                local_files_only=settings.offline,
            )
        )
    model = PocketTTS(path, providers=["CPUExecutionProvider"], num_threads=settings.num_threads)
    if model.config.language not in ("en", "english"):
        raise ValueError("Use a compatible English base model with an optional Hebrew adapter")
    languages: dict[str, str] = {}
    for voice in model.voices():
        language = (
            model.config.voice_languages.get(voice)
            if model.config.voice_languages is not None
            else "en"
        )
        if language not in ("en", "he"):
            raise ValueError(f"Unsupported or missing language for voice {voice!r}: {language!r}")
        languages[voice] = language
    renikud_path = None
    if "he" in languages.values():
        if model.config.lora is None or model.config.max_decode_steps < 2:
            raise ValueError("Hebrew voices require a compatible adapter with two decode steps")
        if settings.renikud_model_path:
            renikud_path = Path(settings.renikud_model_path)
            if not renikud_path.is_file():
                raise FileNotFoundError(f"Renikud model does not exist: {renikud_path}")
        else:
            renikud_path = Path(
                hf_hub_download(
                    repo_id=RENIKUD_REPO,
                    filename=RENIKUD_FILENAME,
                    revision=RENIKUD_REVISION,
                    cache_dir=data_dir / "huggingface",
                    local_files_only=settings.offline,
                )
            )
        from pocket_tts_onnx import phonemize_mixed

        _LOGGER.info("Loading Hebrew grapheme-to-phoneme model")
        phonemize_mixed("\u05e9\u05dc\u05d5\u05dd", model=renikud_path)
    engine: Engine = PocketEngine(model, languages, renikud_path)
    if settings.voice not in engine.voices():
        raise ValueError(f"Unknown default voice {settings.voice!r}; available: {engine.voices()}")
    if engine.sample_rate <= 0:
        raise ValueError("Model sample rate must be positive")
    return engine


def pcm16(samples: NDArray[np.float32]) -> bytes:
    if samples.ndim != 1 or not np.isfinite(samples).all():
        raise ValueError("Model output must be finite mono samples")
    return np.rint(np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()
