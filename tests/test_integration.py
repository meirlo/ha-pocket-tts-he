import asyncio
import os
from pathlib import Path

import numpy as np
import pytest
from test_service import running_server, synthesize
from wyoming.audio import AudioChunk
from wyoming.tts import Synthesize
from wyoming_pocket_tts.backend import load_engine
from wyoming_pocket_tts.settings import Settings


@pytest.mark.integration
@pytest.mark.skipif(os.environ.get("POCKET_TTS_SMOKE") != "1", reason="Opt-in model download")
@pytest.mark.parametrize("offline", [False, True])
async def test_real_model_over_wyoming(offline: bool) -> None:
    engine = await asyncio.to_thread(load_engine, Settings(offline=offline), Path(".cache"))
    assert "alba" in engine.voices()
    assert engine.sample_rate == 24000
    async with running_server(engine) as port:
        events = await synthesize(
            port, Synthesize("Hello from Home Assistant.").event(), timeout=120
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
