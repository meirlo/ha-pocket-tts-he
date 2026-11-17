import asyncio
import io
import json
import logging
import socket
from pathlib import Path

import pytest
from test_service import FakeEngine, running_server, synthesize
from wyoming.tts import Synthesize
from wyoming_pocket_tts import discovery


@pytest.mark.parametrize(
    "hostname", ["local-pocket-tts", "a1b2c3d4-pocket-tts"]
)
def test_supervisor_discovery_uses_internal_hostname(
    monkeypatch: pytest.MonkeyPatch, hostname: str
) -> None:
    requests = []

    class Opener:
        def open(self, request, timeout):
            requests.append(request)
            assert timeout == 10
            assert request.get_header("Authorization") == "Bearer test-token"
            data = (
                {"hostname": hostname, "network": {"10200/tcp": 10400}}
                if request.full_url.endswith("/addons/self/info")
                else {"uuid": "discovery-id"}
            )
            return io.BytesIO(json.dumps({"result": "ok", "data": data}).encode())

    def build_opener(proxy):
        assert proxy.proxies == {}
        return Opener()

    monkeypatch.setattr(discovery, "build_opener", build_opener)
    discovery.register_discovery("test-token", 10200)
    assert requests[0].full_url == "http://supervisor/addons/self/info"
    assert requests[0].get_method() == "GET"
    assert requests[1].full_url == "http://supervisor/discovery"
    assert requests[1].get_method() == "POST"
    assert json.loads(requests[1].data) == {
        "service": "wyoming", "config": {"uri": f"tcp://{hostname}:10200"}
    }


@pytest.mark.parametrize(
    "response",
    [
        {"result": "error", "message": "sensitive API content"},
        {"result": "ok", "data": None},
        {"result": "ok", "data": {"hostname": "http://invalid"}},
        {"result": "ok", "data": {}},
    ],
)
def test_invalid_supervisor_response_is_not_silent(
    monkeypatch: pytest.MonkeyPatch, response: dict[str, object]
) -> None:
    class Opener:
        def open(self, request, timeout):
            return io.BytesIO(json.dumps(response).encode())

    monkeypatch.setattr(discovery, "build_opener", lambda *args: Opener())
    with pytest.raises(discovery.DiscoveryError) as error:
        discovery.register_discovery("test-token", 10200)
    assert "sensitive API content" not in str(error.value)


async def test_publication_retries_and_manual_synthesis_remains_available(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    attempts = []

    def register(token: str, port: int) -> None:
        attempts.append((token, port))
        raise discovery.DiscoveryError("Supervisor unavailable")

    async def no_delay(seconds: float) -> None:
        pass

    monkeypatch.setattr(discovery, "register_discovery", register)
    monkeypatch.setattr(discovery.asyncio, "sleep", no_delay)
    async with running_server(FakeEngine()) as port:
        await discovery.publish_discovery("test-token", f"tcp://0.0.0.0:{port}")
        assert attempts == [("test-token", port)] * 5
        assert (await synthesize(port, Synthesize("Hello").event()))[-1].type == "audio-stop"
    assert "manual Wyoming setup remains available" in caplog.text
    assert "test-token" not in caplog.text


async def test_discovery_retries_then_succeeds(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    attempts = []

    def register(token: str, port: int) -> None:
        attempts.append(port)
        if len(attempts) == 1:
            raise discovery.DiscoveryError("Supervisor unavailable")

    async def no_delay(seconds: float) -> None:
        pass

    monkeypatch.setattr(discovery, "register_discovery", register)
    monkeypatch.setattr(discovery.asyncio, "sleep", no_delay)
    caplog.set_level(logging.INFO)
    async with running_server(FakeEngine()) as port:
        await discovery.publish_discovery("test-token", f"tcp://127.0.0.1:{port}")
    assert attempts == [port, port]
    assert "Published Wyoming discovery" in caplog.text
    assert "manual Wyoming setup remains available" not in caplog.text


async def test_service_publishes_only_after_listener_is_ready_and_skips_standalone(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    from wyoming_pocket_tts import __main__ as service

    monkeypatch.setattr(service, "load_engine", lambda *args: FakeEngine())
    caplog.set_level(logging.INFO)
    published = asyncio.Event()
    loop = asyncio.get_running_loop()
    calls = []

    def register(token: str, port: int) -> None:
        calls.append((token, port))
        loop.call_soon_threadsafe(published.set)

    monkeypatch.setattr(discovery, "register_discovery", register)
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    monkeypatch.setenv("SUPERVISOR_TOKEN", "test-token")
    serving = asyncio.create_task(service.serve(None, tmp_path, f"tcp://0.0.0.0:{port}"))
    try:
        await asyncio.wait_for(published.wait(), 5)
        assert (await synthesize(port, Synthesize("Hello").event()))[-1].type == "audio-stop"
        assert calls == [("test-token", port)]
        assert "Published Wyoming discovery" in caplog.text
    finally:
        serving.cancel()
        with pytest.raises(asyncio.CancelledError):
            await serving

    monkeypatch.delenv("SUPERVISOR_TOKEN")
    serving = asyncio.create_task(service.serve(None, tmp_path, f"tcp://0.0.0.0:{port}"))
    try:
        await discovery._wait_until_ready("127.0.0.1", port)
        assert (await synthesize(port, Synthesize("Hello").event()))[-1].type == "audio-stop"
        assert calls == [("test-token", port)]
    finally:
        serving.cancel()
        with pytest.raises(asyncio.CancelledError):
            await serving
