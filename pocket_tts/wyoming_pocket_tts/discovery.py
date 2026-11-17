import asyncio
import json
import logging
import re
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

from wyoming.event import async_read_event, async_write_event
from wyoming.info import Describe, Info

_LOGGER = logging.getLogger(__name__)


class DiscoveryError(RuntimeError):
    pass


def register_discovery(token: str, port: int) -> None:
    # Keep the Supervisor credential on its internal network, never on an HTTP proxy.
    opener = build_opener(ProxyHandler({}))

    def request(path: str, body: dict[str, object] | None = None) -> dict[str, object]:
        req = Request(
            f"http://supervisor{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        with opener.open(req, timeout=10) as response:
            result = json.load(response)
        if not isinstance(result, dict) or result.get("result") != "ok":
            raise DiscoveryError(f"Supervisor rejected {path}")
        data = result.get("data")
        if not isinstance(data, dict):
            raise DiscoveryError(f"Invalid Supervisor response for {path}")
        return data

    info = request("/addons/self/info")
    hostname = info.get("hostname")
    if not isinstance(hostname, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.-]*", hostname):
        raise DiscoveryError("Supervisor did not return a valid app hostname")
    result = request(
        "/discovery",
        {"service": "wyoming", "config": {"uri": f"tcp://{hostname}:{port}"}},
    )
    if not isinstance(result.get("uuid"), str) or not result["uuid"]:
        raise DiscoveryError("Supervisor discovery response is missing a uuid")


async def _wait_until_ready(host: str, port: int) -> None:
    while True:
        try:
            reader, writer = await asyncio.open_connection(host, port)
        except OSError:
            await asyncio.sleep(0.1)
            continue
        try:
            await async_write_event(Describe().event(), writer)
            event = await async_read_event(reader)
            if event is None or not Info.is_type(event.type) or not Info.from_event(event).tts:
                raise DiscoveryError("Wyoming listener did not advertise TTS")
            return
        finally:
            writer.close()
            await writer.wait_closed()


async def publish_discovery(token: str, uri: str) -> None:
    """Best-effort discovery; failures are visible without disabling manual TTS."""
    address = urlparse(uri)
    if address.scheme != "tcp" or address.hostname is None or address.port is None:
        _LOGGER.warning("Supervisor discovery requires a TCP listener; use manual setup")
        return
    host = address.hostname
    if host == "0.0.0.0":
        host = "127.0.0.1"
    elif host == "::":
        host = "::1"
    try:
        await asyncio.wait_for(_wait_until_ready(host, address.port), timeout=30)
    except (OSError, TimeoutError, ValueError, DiscoveryError) as error:
        _LOGGER.error("Supervisor discovery readiness check failed: %s; use manual setup", error)
        return
    for attempt in range(1, 6):
        try:
            await asyncio.to_thread(register_discovery, token, address.port)
        except (URLError, OSError, ValueError, DiscoveryError) as error:
            _LOGGER.warning("Supervisor discovery attempt %s/5 failed: %s", attempt, error)
            if attempt < 5:
                await asyncio.sleep(2)
        else:
            _LOGGER.info("Published Wyoming discovery to Home Assistant")
            return
    _LOGGER.error("Supervisor discovery failed; manual Wyoming setup remains available")
