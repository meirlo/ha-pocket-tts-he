import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Attribution, Describe, Info, TtsProgram, TtsVoice
from wyoming.server import AsyncEventHandler
from wyoming.tts import Synthesize

from . import __version__
from .backend import Engine, pcm16
from .settings import Settings

_LOGGER = logging.getLogger(__name__)
ATTRIBUTION = Attribution(
    name="thewh1teagle / Kyutai",
    url="https://github.com/thewh1teagle/pocket-tts-onnx",
)


def make_info(engine: Engine, settings: Settings) -> Info:
    names = engine.voices()
    if settings.voice not in names:
        raise ValueError(f"Unknown default voice {settings.voice!r}; available: {names}")
    names = [settings.voice, *sorted(name for name in names if name != settings.voice)]
    return Info(
        tts=[
            TtsProgram(
                name="pocket-tts",
                description="English Pocket TTS ONNX (CC BY 4.0)",
                attribution=ATTRIBUTION,
                installed=True,
                version=__version__,
                supports_synthesize_streaming=False,
                voices=[
                    TtsVoice(
                        name=name,
                        description=f"Pocket TTS English voice: {name}",
                        attribution=ATTRIBUTION,
                        installed=True,
                        version=None,
                        languages=["en"],
                    )
                    for name in names
                ],
            )
        ]
    )


class PocketEventHandler(AsyncEventHandler):
    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        *,
        engine: Engine,
        settings: Settings,
        info: Info,
        lock: asyncio.Lock,
        executor: ThreadPoolExecutor,
        handler_tasks: set[asyncio.Task[None]] | None = None,
    ) -> None:
        super().__init__(reader, writer)
        self.engine = engine
        self.settings = settings
        self.info = info
        self.lock = lock
        self.executor = executor
        self.handler_tasks = handler_tasks

    async def run(self) -> None:
        task = asyncio.current_task()
        assert task is not None
        if self.handler_tasks is not None:
            self.handler_tasks.add(task)
        try:
            await super().run()
        finally:
            if self.handler_tasks is not None:
                self.handler_tasks.discard(task)

    async def write_event(self, event: Event) -> None:
        # Bound backpressure so a stalled client cannot hold the model indefinitely.
        await asyncio.wait_for(super().write_event(event), timeout=30)

    async def handle_event(self, event: Event) -> bool:
        if Describe.is_type(event.type):
            await self.write_event(self.info.event())
            return True
        if not Synthesize.is_type(event.type):
            if event.type.startswith("synthesize-"):
                await self.write_event(
                    Error(
                        text="Streaming text requests are not supported; send synthesize",
                        code="unsupported-event",
                    ).event()
                )
                return False
            return True

        try:
            request = Synthesize.from_event(event)
            voice = self.validate_request(request)
            await self.synthesize(request.text, voice)
        except (ConnectionError, TimeoutError):
            _LOGGER.warning("Client disconnected or stopped reading during synthesis")
            return False
        except Exception as error:
            # Protocol boundary: report failed/partial synthesis, never a successful audio-stop.
            _LOGGER.exception("Synthesis failed")
            await self.write_event(Error(text=str(error), code="synthesis-failed").event())
            return False
        return True

    def validate_request(self, request: Synthesize) -> str:
        if not isinstance(request.text, str) or not request.text.strip():
            raise ValueError("Text must be a non-empty string")
        if len(request.text) > self.settings.max_text_length:
            raise ValueError(f"Text exceeds {self.settings.max_text_length} characters")
        if request.text_format not in (None, "text"):
            raise ValueError("Only plain text is supported (not SSML)")
        voice = self.settings.voice
        if request.voice is not None:
            if request.voice.speaker is not None:
                raise ValueError("Speaker selection is not supported; select a voice by name")
            language = request.voice.language
            if language is not None:
                if (
                    not isinstance(language, str)
                    or language.lower().replace("_", "-").split("-")[0] != "en"
                ):
                    raise ValueError("Only English is supported")
            if request.voice.name is not None:
                voice = request.voice.name
        if voice not in self.engine.voices():
            raise ValueError(f"Unknown voice {voice!r}; available: {self.engine.voices()}")
        return voice

    async def synthesize(self, text: str, voice: str) -> None:
        loop = asyncio.get_running_loop()
        async with self.lock:
            # A single worker also serializes cleanup with any in-flight, cancelled step.
            stream = self.engine.stream(text, voice=voice)
            samples_sent = 0
            started = False
            try:
                while True:
                    samples = await loop.run_in_executor(self.executor, partial(next, stream, None))
                    if samples is None:
                        break
                    audio = pcm16(samples)
                    if not audio:
                        continue
                    if not started:
                        await self.write_event(
                            AudioStart(
                                rate=self.engine.sample_rate, width=2, channels=1, timestamp=0
                            ).event()
                        )
                        started = True
                    await self.write_event(
                        AudioChunk(
                            rate=self.engine.sample_rate,
                            width=2,
                            channels=1,
                            audio=audio,
                            timestamp=samples_sent * 1000 // self.engine.sample_rate,
                        ).event()
                    )
                    samples_sent += len(audio) // 2
                if not started:
                    raise RuntimeError("Model generated no audio")
                await self.write_event(
                    AudioStop(timestamp=samples_sent * 1000 // self.engine.sample_rate).event()
                )
            finally:
                close = getattr(stream, "close", None)
                if close is not None:
                    await loop.run_in_executor(self.executor, close)
