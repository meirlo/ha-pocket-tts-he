# Pocket TTS for Home Assistant

A standalone Home Assistant app (formerly "add-on") that serves
[Pocket TTS ONNX](https://github.com/thewh1teagle/pocket-tts-onnx) through the
[Wyoming protocol](https://www.home-assistant.io/integrations/wyoming/).
Synthesis runs locally on CPU, without PyTorch or a cloud speech API.

The initial version supports **English**, the model's embedded voices, and
streaming **24 kHz mono, signed 16-bit little-endian PCM** audio. It accepts
Wyoming `describe` and `synthesize` requests. SSML, streaming text-input
events, voice cloning and Hebrew adapters are not exposed.

## Install

Requires **Home Assistant OS** or another installation with Supervisor/app
support. Home Assistant Container/Core users can run the standalone container
and connect the same Wyoming integration.

This project has not been published to GitHub yet. For local installation:

1. Copy the entire `pocket_tts` folder from this repository into the Home
   Assistant local apps directory, traditionally `/addons/pocket_tts`
   (for example, through the Samba or SSH app).
2. Open **Settings > Apps** (called **Add-ons** in older releases), open the
   app store, and reload/check for updates.
3. Find **Pocket TTS** under **Local apps**, install it, and start it.
4. Wait for `Model ready` in its log before connecting Home Assistant.

The image builds on the device, so installation requires internet access to
Docker Hub, GitHub and PyPI. The first start downloads the pinned English
model (~228 MB) from Hugging Face into persistent `/data/huggingface`; later
starts reuse it. Allow several minutes for the first build/download.
Plan for at least 1 GB of free storage and a 64-bit system with several GB
of RAM available; actual memory and synthesis speed depend on hardware.

Once this repository is hosted, add its actual Git URL using the app store's
**Repositories** dialog. `repository.yaml` and the add-on folder are already
provided; no fictional repository URL or prebuilt image is configured.

## Connect Home Assistant

1. Open **Settings > Devices & services > Add integration > Wyoming Protocol**.
2. Set **Host** to your Home Assistant machine's LAN IP, and **Port** to `10200`
   (or the host port selected in the app's Network settings).
3. Open **Settings > Voice assistants**, edit/create an assistant, choose
   English and select the new **Pocket TTS** text-to-speech provider and voice.

Discovery is manual, not automatic; the service requests no Supervisor API
permissions. Piper also usually uses `10200`, so change one app's **host
port** if running both; two apps cannot bind the same host port. The internal
Pocket TTS port remains `10200`.

You can also call Home Assistant's `tts.speak` action with the TTS entity
created by the integration and a media player. Home Assistant fetches the
audio over Wyoming; the add-on does not access your sound hardware.

**Wyoming TCP has no authentication or encryption.** Keep the port on your
trusted LAN; never forward it to the internet.

## Configuration

See [the add-on documentation](pocket_tts/DOCS.md) for all options, voices,
offline use, backups and troubleshooting.

## Development / standalone

Python **3.13** is required by the pinned upstream package. All production
dependencies, including the complete transitive set, are pinned in
`pocket_tts/requirements.txt`. A previous upstream revision is intentional:
the current revision adds an unlicensed dependency; see
[attribution and compatibility notes](pocket_tts/NOTICE.md).

From this repository in PowerShell (with Python 3.13 installed):

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m mypy
Set-Location pocket_tts
..\.venv\Scripts\python -m wyoming_pocket_tts --data-dir ..\.cache --uri tcp://127.0.0.1:10200
```

On Linux, use `python3.13 -m venv .venv` and `.venv/bin/python` instead.
Run the server from `pocket_tts` with a persistent `--data-dir`, and bind
`tcp://0.0.0.0:10200` when Home Assistant is on a different host. `--options`
accepts the same JSON keys as the add-on options; omitting it uses defaults.
Startup/configuration/model failures are logged and exit nonzero.

For the opt-in real-model Wyoming smoke test (downloads ~228 MB), from the
repository root:

```powershell
$env:POCKET_TTS_SMOKE = "1"
.venv\Scripts\python -m pytest -q tests\test_integration.py
```

Build the standalone container with Docker:

```powershell
docker build -t pocket-tts pocket_tts
docker run --rm -p 10200:10200 -v pocket-tts-data:/data pocket-tts --data-dir /data
```

The overridden command above intentionally omits `--options`: outside
Supervisor there is no `/data/options.json`.

To update dependencies, edit `pocket_tts/requirements.in` and regenerate
using `uv pip compile --python-version 3.13 --universal
pocket_tts/requirements.in --output-file pocket_tts/requirements.txt`.
Recheck upstream API/model compatibility and both Linux wheel sets before
changing an upstream revision or declaring another architecture.

Only **amd64** and **aarch64** are declared: the Python 3.13 runtime and
native dependencies provide glibc Linux wheels for these platforms.
The Debian Bookworm image supplies glibc; Alpine/musl and 32-bit ARM/x86
are not supported. Wheel availability is not a hardware performance
guarantee. CI builds both container architectures; a real Home Assistant
installation remains the final deployment check.

## License

Original wrapper and packaging: [MIT](pocket_tts/LICENSE).
Pocket TTS ONNX and its downloaded model: **CC BY 4.0**.
See [NOTICE](pocket_tts/NOTICE.md) for attribution and third-party obligations.
