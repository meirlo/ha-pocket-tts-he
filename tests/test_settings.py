import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from wyoming_pocket_tts.backend import MODEL_FILENAME, MODEL_REPO, MODEL_REVISION, load_engine
from wyoming_pocket_tts.settings import Settings, load_settings


def test_options_file(tmp_path: Path) -> None:
    path = tmp_path / "options.json"
    path.write_text(json.dumps({"voice": "cosette", "num_threads": 4}), encoding="utf-8")
    assert load_settings(path) == Settings(voice="cosette", num_threads=4)


@pytest.mark.parametrize(
    "option",
    [
        {"num_threads": 0},
        {"num_threads": True},
        {"num_threads": 33},
        {"max_text_length": -1},
        {"offline": "false"},
        {"voice": ""},
        {"model_path": 123},
        {"log_level": "trace"},
    ],
)
def test_invalid_options(option: dict[str, object], tmp_path: Path) -> None:
    path = tmp_path / "options.json"
    path.write_text(json.dumps(option), encoding="utf-8")
    with pytest.raises(ValueError):
        load_settings(path)


def test_missing_options_file_does_not_silently_use_defaults(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_settings(tmp_path / "missing.json")


def test_model_cache_revision_and_offline_mode(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    import huggingface_hub
    import pocket_tts_onnx
    from test_service import FakeEngine

    download_calls = []
    load_calls = []

    def download(**kwargs: object) -> str:
        download_calls.append(kwargs)
        return str(tmp_path / "cached.onnx")

    def load(*args: object, **kwargs: object) -> FakeEngine:
        load_calls.append((args, kwargs))
        engine = FakeEngine()
        engine.config = SimpleNamespace(language="english", lora=None)
        return engine

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", download)
    monkeypatch.setattr(pocket_tts_onnx, "PocketTTS", load)
    load_engine(Settings(offline=True, num_threads=4), tmp_path)
    assert download_calls == [
        {
            "repo_id": MODEL_REPO,
            "filename": MODEL_FILENAME,
            "revision": MODEL_REVISION,
            "cache_dir": tmp_path / "huggingface",
            "local_files_only": True,
        }
    ]
    assert load_calls[0][1] == {"providers": ["CPUExecutionProvider"], "num_threads": 4}

    local_model = tmp_path / "custom.onnx"
    local_model.touch()
    load_engine(Settings(model_path=str(local_model)), tmp_path)
    assert len(download_calls) == 1
    with pytest.raises(FileNotFoundError):
        load_engine(Settings(model_path=str(tmp_path / "missing.onnx")), tmp_path)
    with pytest.raises(ValueError, match="Unknown default voice"):
        load_engine(Settings(voice="missing"), tmp_path)


@pytest.mark.parametrize("language,lora", [("he", None), ("english", {})])
def test_incompatible_local_model_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, language: str, lora: object
) -> None:
    import pocket_tts_onnx
    from test_service import FakeEngine

    local_model = tmp_path / "custom.onnx"
    local_model.touch()

    def load(*args: object, **kwargs: object) -> FakeEngine:
        engine = FakeEngine()
        engine.config = SimpleNamespace(language=language, lora=lora)
        return engine

    monkeypatch.setattr(pocket_tts_onnx, "PocketTTS", load)
    with pytest.raises(ValueError, match="without phoneme adapters"):
        load_engine(Settings(model_path=str(local_model)), tmp_path)
