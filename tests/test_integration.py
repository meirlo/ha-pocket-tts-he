import asyncio
import os
import socket
from pathlib import Path

import numpy as np
import pytest
from test_service import running_server, synthesize
from wyoming.audio import AudioChunk
from wyoming.tts import Synthesize, SynthesizeVoice
from wyoming_pocket_tts.backend import load_engine
from wyoming_pocket_tts.settings import Settings


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get("POCKET_TTS_SMOKE") != "1", reason="Opt-in model download")
@pytest.mark.parametrize(
    "voice,text",
    [
        ("alba", "Hello from Home Assistant."),
        ("omer", "\u05e9\u05dc\u05d5\u05dd \u05e2\u05d5\u05dc\u05dd."),
        ("liat", "\u05e9\u05dc\u05d5\u05dd Google. \u05d4\u05e9\u05e2\u05d4 12:30."),
    ],
)
async def test_real_model_over_wyoming(
    voice: str, text: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = await asyncio.to_thread(load_engine, Settings(), Path(".cache"))
    del engine
    attempts = []

    def reject_connection(*args: object, **kwargs: object) -> None:
        attempts.append((args, kwargs))
        raise AssertionError("Cached startup must not attempt a network connection")

    with monkeypatch.context() as offline:
        offline.setattr(socket.socket, "connect", reject_connection)
        offline.setattr(socket.socket, "connect_ex", reject_connection)
        engine = await asyncio.to_thread(load_engine, Settings(), Path(".cache"))
    assert not attempts
    assert "alba" in engine.voices()
    assert engine.voice_language("omer") == "he"
    assert engine.voice_language("liat") == "he"
    assert engine.sample_rate == 24000
    async with running_server(engine) as port:
        events = await synthesize(
            port,
            Synthesize(text, voice=SynthesizeVoice(name=voice)).event(),
            timeout=120,
        )
    assert events[0].type == "audio-start"
    assert events[-1].type == "audio-stop"
    chunks = [
        AudioChunk.from_event(event) for event in events if event.type == "audio-chunk"
    ]
    assert len(chunks) > 1
    assert all((chunk.rate, chunk.width, chunk.channels) == (24000, 2, 1) for chunk in chunks)
    audio = b"".join(chunk.audio for chunk in chunks)
    samples = np.frombuffer(audio, dtype="<i2")
    assert len(samples) > 2400
    assert np.max(np.abs(samples.astype(np.int32))) > 100
