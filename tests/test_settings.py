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


@pytest.mark.parametrize("offline", [False, True])
def test_legacy_offline_option_is_migrated(
    offline: bool, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "options.json"
    path.write_text(json.dumps({"voice": "cosette", "offline": offline}), encoding="utf-8")
    assert load_settings(path) == Settings(voice="cosette")
    assert "offline option is obsolete and ignored" in caplog.text


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
        {"renikud_model_path": 123},
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


def test_cached_model_uses_pinned_revision_without_network(
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
        engine.config = SimpleNamespace(language="english", lora=None, voice_languages=None)
        return engine

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", download)
    monkeypatch.setattr(pocket_tts_onnx, "PocketTTS", load)
    load_engine(Settings(num_threads=4), tmp_path)
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


@pytest.mark.parametrize(
    "language,lora,voice_languages,steps",
    [
        ("he", None, None, 1),
        ("english", None, {"cosette": "he", "alba": "en"}, 2),
        ("english", {}, {"cosette": "he", "alba": "en"}, 1),
        ("english", {}, {"cosette": "fr", "alba": "en"}, 2),
    ],
)
def test_incompatible_local_model_is_rejected(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, language: str, lora: object,
    voice_languages: dict[str, str] | None, steps: int
) -> None:
    import pocket_tts_onnx
    from test_service import FakeEngine

    local_model = tmp_path / "custom.onnx"
    local_model.touch()

    def load(*args: object, **kwargs: object) -> FakeEngine:
        engine = FakeEngine()
        engine.config = SimpleNamespace(
            language=language, lora=lora, voice_languages=voice_languages, max_decode_steps=steps
        )
        return engine

    monkeypatch.setattr(pocket_tts_onnx, "PocketTTS", load)
    with pytest.raises(ValueError):
        load_engine(Settings(model_path=str(local_model)), tmp_path)


@pytest.mark.parametrize(
    "missing",
    [(), (MODEL_FILENAME,), ("model.onnx",), (MODEL_FILENAME, "model.onnx")],
)
def test_hebrew_models_download_only_missing_files_and_support_local_paths(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, missing: tuple[str, ...]
) -> None:
    import huggingface_hub
    import pocket_tts_onnx
    from huggingface_hub.errors import LocalEntryNotFoundError
    from test_service import BilingualEngine
    from wyoming_pocket_tts.backend import RENIKUD_FILENAME, RENIKUD_REPO, RENIKUD_REVISION

    model = BilingualEngine()
    model.config = SimpleNamespace(
        language="english", lora={}, max_decode_steps=2,
        voice_languages={"alba": "en", "cosette": "en", "liat": "he", "omer": "he"},
    )
    downloads = []
    preprocessed = []
    uncached = set(missing)

    def download(**kwargs: object) -> str:
        downloads.append(kwargs)
        filename = kwargs["filename"]
        if filename in uncached:
            if kwargs["local_files_only"]:
                raise LocalEntryNotFoundError("Model is not cached")
            uncached.remove(filename)
        return str(tmp_path / "cached.onnx")

    def phonemize(text: str, *, model: Path) -> str:
        preprocessed.append((text, model))
        return "ipa"

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", download)
    monkeypatch.setattr(pocket_tts_onnx, "PocketTTS", lambda *args, **kwargs: model)
    monkeypatch.setattr(pocket_tts_onnx, "phonemize_mixed", phonemize)
    engine = load_engine(Settings(), tmp_path)
    assert engine.voice_language("omer") == "he"
    expected = []
    for repo, filename, revision in (
        (MODEL_REPO, MODEL_FILENAME, MODEL_REVISION),
        (RENIKUD_REPO, RENIKUD_FILENAME, RENIKUD_REVISION),
    ):
        options = {
            "repo_id": repo, "filename": filename, "revision": revision,
            "cache_dir": tmp_path / "huggingface", "local_files_only": True,
        }
        expected.append(options)
        if filename in missing:
            expected.append({**options, "local_files_only": False})
    assert downloads == expected
    assert preprocessed == [("\u05e9\u05dc\u05d5\u05dd", tmp_path / "cached.onnx")]
    downloads.clear()
    load_engine(Settings(), tmp_path)
    assert len(downloads) == 2
    assert all(call["local_files_only"] for call in downloads)
    local_model = tmp_path / "custom.onnx"
    local_model.touch()
    renikud = tmp_path / "renikud.onnx"
    renikud.touch()
    load_engine(
        Settings(model_path=str(local_model), renikud_model_path=str(renikud)),
        tmp_path,
    )
    assert len(downloads) == 2
    assert preprocessed[-1][1] == renikud
    with pytest.raises(FileNotFoundError, match="Renikud"):
        load_engine(
            Settings(model_path=str(local_model), renikud_model_path=str(tmp_path / "missing")),
            tmp_path,
        )


@pytest.mark.parametrize("failure", ["cache", "download"])
def test_model_cache_and_download_errors_are_not_hidden(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, failure: str
) -> None:
    import huggingface_hub
    from huggingface_hub.errors import LocalEntryNotFoundError

    calls = []

    def download(**kwargs: object) -> str:
        calls.append(kwargs["local_files_only"])
        if failure == "download" and kwargs["local_files_only"]:
            raise LocalEntryNotFoundError("Model is not cached")
        raise OSError("Model is inaccessible")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", download)
    with pytest.raises(OSError, match="Model is inaccessible"):
        load_engine(Settings(), tmp_path)
    assert calls == ([True] if failure == "cache" else [True, False])


def test_hebrew_preprocessing_and_adapter_do_not_change_english(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import numpy as np
    import pocket_tts_onnx
    from test_service import BilingualEngine
    from wyoming_pocket_tts.backend import PocketEngine

    calls = []
    preprocessed = []

    class Model(BilingualEngine):
        def stream(self, text: str, voice: str, **kwargs: object):
            calls.append((text, voice, kwargs))
            yield np.ones(10, dtype=np.float32)

    def phonemize(text: str, *, model: Path) -> str:
        preprocessed.append((text, model))
        return "ipa"

    monkeypatch.setattr(pocket_tts_onnx, "phonemize_mixed", phonemize)
    engine = PocketEngine(Model(), {"omer": "he", "alba": "en"}, Path("renikud.onnx"))
    list(engine.stream("\u05e9\u05dc\u05d5\u05dd Google", voice="omer"))
    list(engine.stream("Hello", voice="alba"))
    assert preprocessed == [("\u05e9\u05dc\u05d5\u05dd Google", Path("renikud.onnx"))]
    assert calls == [
        ("ipa", "omer", {"phonemes": True, "decode_steps": 2}),
        ("Hello", "alba", {}),
    ]

    monkeypatch.setattr(pocket_tts_onnx, "phonemize_mixed", lambda *args, **kwargs: "")
    with pytest.raises(ValueError, match="no speakable text"):
        list(engine.stream("text", voice="omer"))
    assert len(calls) == 2
