import argparse
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from pathlib import Path

from wyoming.server import AsyncServer

from .backend import load_engine
from .server import PocketEventHandler, make_info
from .settings import load_settings


async def serve(options: Path | None, data_dir: Path, uri: str) -> None:
    settings = load_settings(options)
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    server = AsyncServer.from_uri(uri)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="pocket-tts") as executor:
        engine = await asyncio.get_running_loop().run_in_executor(
            executor, partial(load_engine, settings, data_dir)
        )
        info = make_info(engine, settings)
        handler_tasks: set[asyncio.Task[None]] = set()
        logging.getLogger(__name__).info(
            "Model ready; starting Wyoming server at %s; voices: %s",
            uri,
            ", ".join(engine.voices()),
        )
        try:
            await server.run(
                partial(
                    PocketEventHandler,
                    engine=engine,
                    settings=settings,
                    info=info,
                    lock=asyncio.Lock(),
                    executor=executor,
                    handler_tasks=handler_tasks,
                )
            )
        finally:
            await server.stop()
            # Wyoming closes sockets on stop but does not await inference cleanup.
            results = await asyncio.gather(*list(handler_tasks), return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logging.getLogger(__name__).error(
                        "Wyoming connection failed during shutdown",
                        exc_info=(type(result), result, result.__traceback__),
                    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Pocket TTS ONNX Wyoming server")
    parser.add_argument("--uri", default="tcp://0.0.0.0:10200")
    parser.add_argument("--options", type=Path, help="Home Assistant-style JSON options file")
    parser.add_argument("--data-dir", type=Path, default=Path("/data"))
    args = parser.parse_args()
    try:
        asyncio.run(serve(args.options, args.data_dir, args.uri))
    except KeyboardInterrupt:
        pass
    except Exception:
        logging.getLogger(__name__).exception("Pocket TTS startup/server failed")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
