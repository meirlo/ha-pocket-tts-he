import asyncio
import threading
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from functools import partial
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event, async_read_event, async_write_event
from wyoming.info import Describe, Info
from wyoming.server import AsyncTcpServer, HandlerFactory
from wyoming.tts import Synthesize, SynthesizeVoice
from wyoming_pocket_tts.backend import Engine, pcm16
from wyoming_pocket_tts.server import PocketEventHandler, make_info
from wyoming_pocket_tts.settings import Settings


class FakeEngine:
    sample_rate = 24000

    def __init__(self, fail: bool = False, empty: bool = False) -> None:
        self.calls: list[tuple[str, str]] = []
        self.closed = 0
        self.fail = fail
        self.empty = empty

    def voices(self) -> list[str]:
        return ["cosette", "alba"]

    def stream(self, text: str, voice: str) -> Iterator[NDArray[np.float32]]:
        self.calls.append((text, voice))
        try:
            if self.empty:
                return
            yield np.array([-2, -1, 0, 1, 2], dtype=np.float32)
            if self.fail:
                raise RuntimeError("inference failed")
            yield np.ones(2400, dtype=np.float32) * 0.25
        finally:
            self.closed += 1


@asynccontextmanager
async def running_server(engine: Engine, settings: Settings | None = None) -> AsyncIterator[int]:
    settings = settings or Settings()
    tasks: set[asyncio.Task[None]] = set()
    with ThreadPoolExecutor(max_workers=1) as executor:
        factory = partial(
            PocketEventHandler,
            engine=engine,
            settings=settings,
            info=make_info(engine, settings),
            lock=asyncio.Lock(),
            executor=executor,
        )

        async def connect(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            task = asyncio.current_task()
            assert task is not None
            tasks.add(task)
            try:
                await factory(reader, writer).run()
            finally:
                tasks.remove(task)
                await writer.wait_closed()

        server = await asyncio.start_server(connect, "127.0.0.1", 0)
        try:
            yield server.sockets[0].getsockname()[1]
        finally:
            server.close()
            await server.wait_closed()
            remaining = list(tasks)
            for task in remaining:
                task.cancel()
            await asyncio.gather(*remaining, return_exceptions=True)


async def receive(reader: asyncio.StreamReader, timeout: float = 5) -> Event:
    event = await asyncio.wait_for(async_read_event(reader), timeout)
    assert event is not None
    return event


async def synthesize(port: int, request: Event, timeout: float = 5) -> list[Event]:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    try:
        await async_write_event(request, writer)
        events = []
        while True:
            event = await receive(reader, timeout)
            events.append(event)
            if event.type in ("audio-stop", "error"):
                return events
    finally:
        writer.close()
        await writer.wait_closed()


async def test_describe_and_multiple_requests_on_one_connection() -> None:
    engine = FakeEngine()
    async with running_server(engine, Settings(voice="cosette")) as port:
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        try:
            await async_write_event(Describe().event(), writer)
            info = Info.from_event(await receive(reader))
            assert [voice.name for voice in info.tts[0].voices] == ["cosette", "alba"]
            assert all(voice.languages == ["en"] for voice in info.tts[0].voices)
            assert not info.tts[0].supports_synthesize_streaming
            for _ in range(2):
                await async_write_event(Synthesize("Hello").event(), writer)
                assert AudioStart.is_type((await receive(reader)).type)
                first = AudioChunk.from_event(await receive(reader))
                assert (first.rate, first.width, first.channels) == (24000, 2, 1)
                assert np.frombuffer(first.audio, dtype="<i2").tolist() == [
                    -32767,
                    -32767,
                    0,
                    32767,
                    32767,
                ]
                second = AudioChunk.from_event(await receive(reader))
                assert len(second.audio) == 4800
                assert second.timestamp == 0
                stop = AudioStop.from_event(await receive(reader))
                assert stop.timestamp == 2405 * 1000 // 24000
            assert engine.calls == [("Hello", "cosette"), ("Hello", "cosette")]
        finally:
            writer.close()
            await writer.wait_closed()


async def test_requested_voice_and_english_locale() -> None:
    engine = FakeEngine()
    async with running_server(engine) as port:
        events = await synthesize(
            port,
            Synthesize("Hello", voice=SynthesizeVoice(name="cosette", language="en_US")).event(),
        )
    assert events[-1].type == "audio-stop"
    assert engine.calls == [("Hello", "cosette")]
    assert engine.closed == 1


@pytest.mark.parametrize(
    "event",
    [
        Synthesize("").event(),
        Synthesize(" " * 4).event(),
        Synthesize("x" * 17).event(),
        Synthesize("Hello", voice=SynthesizeVoice(name="unknown")).event(),
        Synthesize("Hello", voice=SynthesizeVoice(language="he")).event(),
        Synthesize("Hello", voice=SynthesizeVoice(speaker="0")).event(),
        Synthesize("<speak>Hello</speak>", text_format="ssml").event(),
        Event(type="synthesize", data={}),
        Event(type="synthesize", data={"text": 123}),
        Event(type="synthesize-start"),
    ],
)
async def test_invalid_requests_return_errors_without_audio(event: Event) -> None:
    engine = FakeEngine()
    async with running_server(engine, Settings(max_text_length=16)) as port:
        events = await synthesize(port, event)
    assert [event.type for event in events] == ["error"]
    assert Error.from_event(events[0]).text
    assert not engine.calls


@pytest.mark.parametrize("empty", [False, True])
async def test_inference_failure_does_not_send_successful_stop(empty: bool) -> None:
    engine = FakeEngine(fail=True, empty=empty)
    async with running_server(engine) as port:
        events = await synthesize(port, Synthesize("Hello").event())
    assert events[-1].type == "error"
    assert not any(event.type == "audio-stop" for event in events)
    assert engine.closed == 1


class BlockingEngine(FakeEngine):
    def __init__(self) -> None:
        super().__init__()
        self.started = threading.Event()
        self.release = threading.Event()
        self.order: list[str] = []

    def stream(self, text: str, voice: str) -> Iterator[NDArray[np.float32]]:
        self.order.append(f"start:{text}")
        try:
            if text == "first":
                self.started.set()
                if not self.release.wait(timeout=5):
                    raise TimeoutError("Test did not release inference")
            yield np.zeros(2400, dtype=np.float32)
        finally:
            self.order.append(f"end:{text}")


async def test_inference_does_not_block_describe_and_serializes_clients() -> None:
    engine = BlockingEngine()
    async with running_server(engine) as port:
        first = asyncio.create_task(synthesize(port, Synthesize("first").event()))
        try:
            assert await asyncio.to_thread(engine.started.wait, 2)
            second = asyncio.create_task(synthesize(port, Synthesize("second").event()))
            reader, writer = await asyncio.open_connection("127.0.0.1", port)
            try:
                await async_write_event(Describe().event(), writer)
                assert (await receive(reader, timeout=1)).type == "info"
                assert engine.order == ["start:first"]
            finally:
                writer.close()
                await writer.wait_closed()
        finally:
            engine.release.set()
        assert (await first)[-1].type == "audio-stop"
        assert (await second)[-1].type == "audio-stop"
    assert engine.order == ["start:first", "end:first", "start:second", "end:second"]


async def test_cancelled_inference_is_closed_before_next_request() -> None:
    engine = BlockingEngine()
    with ThreadPoolExecutor(max_workers=1) as executor:
        lock = asyncio.Lock()
        handler = PocketEventHandler(
            asyncio.StreamReader(),
            None,  # type: ignore[arg-type]
            engine=engine,
            settings=Settings(),
            info=make_info(engine, Settings()),
            lock=lock,
            executor=executor,
        )

        async def discard(event: Event) -> None:
            pass

        handler.write_event = discard  # type: ignore[method-assign]
        first = asyncio.create_task(handler.synthesize("first", "alba"))
        try:
            assert await asyncio.to_thread(engine.started.wait, 2)
            first.cancel()
            second = asyncio.create_task(handler.synthesize("second", "alba"))
            await asyncio.sleep(0)
        finally:
            engine.release.set()
        with pytest.raises(asyncio.CancelledError):
            await first
        await second
    assert engine.order == ["start:first", "end:first", "start:second", "end:second"]


def test_invalid_model_audio_is_rejected() -> None:
    for samples in (np.array([np.nan], dtype=np.float32), np.zeros((1, 3), dtype=np.float32)):
        with pytest.raises(ValueError):
            pcm16(samples)


async def test_shutdown_waits_for_inference_cleanup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from wyoming_pocket_tts import __main__ as service

    engine = BlockingEngine()
    server = AsyncTcpServer("127.0.0.1", 0)
    listening = asyncio.Event()
    stopped = asyncio.Event()
    original_stop = server.stop

    async def run(factory: HandlerFactory) -> None:
        await server.start(factory)
        listening.set()
        await asyncio.Event().wait()

    async def stop() -> None:
        await original_stop()
        stopped.set()

    monkeypatch.setattr(service, "load_engine", lambda *args: engine)
    monkeypatch.setattr(service.AsyncServer, "from_uri", lambda uri: server)
    monkeypatch.setattr(server, "run", run)
    monkeypatch.setattr(server, "stop", stop)
    serving = asyncio.create_task(service.serve(None, tmp_path, "tcp://127.0.0.1:0"))
    writer = None
    try:
        await asyncio.wait_for(listening.wait(), 2)
        assert server._server is not None
        port = server._server.sockets[0].getsockname()[1]
        _, writer = await asyncio.open_connection("127.0.0.1", port)
        await async_write_event(Synthesize("first").event(), writer)
        assert await asyncio.to_thread(engine.started.wait, 2)
        serving.cancel()
        await asyncio.wait_for(stopped.wait(), 2)
        assert not serving.done()
    finally:
        engine.release.set()
        if not stopped.is_set():
            serving.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(serving, 5)
        if writer is not None:
            writer.close()
            await writer.wait_closed()
    assert engine.order == ["start:first", "end:first"]
