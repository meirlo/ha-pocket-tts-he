import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    voice: str = "alba"
    model_path: str = ""
    offline: bool = False
    num_threads: int = 2
    max_text_length: int = 4000
    log_level: str = "info"

    def __post_init__(self) -> None:
        if not isinstance(self.voice, str) or not self.voice.strip():
            raise ValueError("voice must be a non-empty built-in voice name")
        if not isinstance(self.model_path, str):
            raise ValueError("model_path must be a string")
        if not isinstance(self.offline, bool):
            raise ValueError("offline must be a boolean")
        for name, maximum in (("num_threads", 32), ("max_text_length", 16000)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= maximum:
                raise ValueError(f"{name} must be an integer between 1 and {maximum}")
        if self.log_level not in ("debug", "info", "warning", "error"):
            raise ValueError("log_level must be debug, info, warning or error")


def load_settings(path: Path | None) -> Settings:
    if path is None:
        return Settings()
    with path.open(encoding="utf-8") as options_file:
        options = json.load(options_file)
    if not isinstance(options, dict):
        raise ValueError("Options must be a JSON object")
    return Settings(**options)
