import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from .settings import Settings

MODEL_REPO = "thewh1teagle/pocket-tts-onnx"
MODEL_REVISION = "110f5251188e9407b4f724acdd8b0dfd0b20692a"
MODEL_FILENAME = "pocket-tts-english.onnx"
_LOGGER = logging.getLogger(__name__)


class Engine(Protocol):
    @property
    def sample_rate(self) -> int: ...

    def voices(self) -> list[str]: ...

    def stream(self, text: str, voice: str) -> Iterator[NDArray[np.float32]]: ...


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
    if model.config.language not in ("en", "english") or model.config.lora is not None:
        raise ValueError("Only English single-file models without phoneme adapters are supported")
    engine: Engine = model
    if settings.voice not in engine.voices():
        raise ValueError(f"Unknown default voice {settings.voice!r}; available: {engine.voices()}")
    if engine.sample_rate <= 0:
        raise ValueError("Model sample rate must be positive")
    return engine


def pcm16(samples: NDArray[np.float32]) -> bytes:
    if samples.ndim != 1 or not np.isfinite(samples).all():
        raise ValueError("Model output must be finite mono samples")
    return np.rint(np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()
