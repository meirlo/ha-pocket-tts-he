# Pocket TTS for Home Assistant

Give your Home Assistant voice assistant **local English and Hebrew speech**.
Pocket TTS is a Home Assistant app (formerly "add-on") powered by
[Pocket TTS ONNX](https://github.com/thewh1teagle/pocket-tts-onnx), connected through
the [Wyoming integration](https://www.home-assistant.io/integrations/wyoming/).
Speech runs on your CPU: no cloud speech service, API key, or GPU is required.

- **Eight voices:** six English voices and Hebrew voices **omer** and **liat**.
- **Automatic discovery:** confirm the integration after starting the app, without
  entering a host or port.
- **Private, offline speech:** text and audio stay local; models download once.
- **Hebrew and mixed text:** supports Hebrew numbers, dates, times, and English
  words within Hebrew speech. Audio streams as it is generated.

## Before you install

Use **Home Assistant OS** or an installation with Supervisor and app support.
Supported hardware is **64-bit amd64 or aarch64**; 32-bit systems are not supported.
Allow at least **1 GB of free storage** and several GB of available RAM.
Speech speed depends on your CPU; amd64 installation has been tested on Home Assistant.
Home Assistant Container/Core users can use the [standalone container](#development--standalone).

## Install the app

**This repository is private. Use local installation:** Home Assistant's app store
cannot clone this private repository through the shortcut buttons.

1. Download or clone this repository using your GitHub account. Copy the entire
   `pocket_tts` folder into `/addons/pocket_tts` on your Home Assistant host, for
   example through the Samba or SSH app.
2. Open **Settings > Apps > App store** (called **Add-ons** in older releases),
   reload/check for updates, and install **Pocket TTS** under **Local apps**.
3. Start the app and wait for **`Model ready`** in its log.
4. Open **Settings > Devices & services** and confirm the discovered **Pocket TTS**
   Wyoming integration.
5. Open **Settings > Voice assistants**, edit or create an assistant, and choose
   **English** or **Hebrew**, **Pocket TTS** as the text-to-speech provider, and a voice.

**First installation takes several minutes.** The image builds on your device
using Docker Hub, GitHub, and PyPI. First startup downloads approximately **252 MB**
of models from Hugging Face: the speech model (~231 MB) and Hebrew pronunciation
model (~21 MB). Later starts reuse the persistent cache.

### Repository shortcuts

These official shortcuts are for repository-based installation **if the repository
is made public in the future**. They do not work for the current private repository
or a locally installed copy. Add the repository first, then open Pocket TTS and
choose **Install**; both actions require your confirmation.

[![Add app repository to Home Assistant](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fmeirlo%2Fha-pocket-tts-he.git)
[![Open Pocket TTS in Home Assistant](https://my.home-assistant.io/badges/supervisor_addon.svg)](https://my.home-assistant.io/redirect/supervisor_addon/?addon=50e8e570_pocket_tts&repository_url=https%3A%2F%2Fgithub.com%2Fmeirlo%2Fha-pocket-tts-he.git)

For manual repository-based installation, the app store's **Repositories** dialog
uses this exact URL:

```text
https://github.com/meirlo/ha-pocket-tts-he.git
```

The app shortcut matches that repository URL. If you previously added the URL
without `.git`, open Pocket TTS from the app store instead.

## Choose a voice

| Assistant language | Available voices |
| --- | --- |
| English | `alba` (default), `anna`, `cosette`, `javert`, `marius`, `michael` |
| Hebrew | `omer`, `liat` |

Select a voice in your assistant's settings. To change the app's fallback voice,
set **`voice`** in its **Configuration** tab and restart. Home Assistant's selected
voice takes precedence. An English-only custom model will not offer Hebrew voices.

You can also use Home Assistant's **`tts.speak`** action with the integration's TTS
entity and a media player for announcements. The app does not need sound hardware.

## Useful settings and troubleshooting

Keep the defaults for your first start. After the models have downloaded, set
**`offline: true`** to prevent further model downloads. Cached models are excluded
from backups, so a restore needs another download or separately supplied model files.
See [app documentation](pocket_tts/DOCS.md) for configuration, offline use, backups,
local models, and troubleshooting.

**Already using Piper?** Both apps default to host port `10200`. Change one app's
host port in its **Network** settings before starting both. Automatic discovery
uses Pocket TTS's internal port and still works with a different host port.

**No discovery card?** Wait for the model to load and check the app log. You can
always add **Wyoming Protocol** manually under **Devices & services > Add integration**,
using your Home Assistant server's LAN IP and the app's mapped port. Standalone
servers require this manual setup.

**Already connected manually?** Ignore the new discovery card, or remove the manual
entry before confirming discovery, to avoid duplicate TTS entities.

**Keep it on your trusted network.** Wyoming TCP has no authentication or encryption;
never forward its port to the internet.

**Upgrading from 0.1.0:** the default model now includes the Hebrew adapter.
An old English-only cache is not enough for offline startup; start once with
`offline: false` to cache both new files, or supply local models.

## Development / standalone

The service streams 24 kHz mono PCM16 audio. SSML, streaming text input, and voice
cloning are not exposed.

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

For the opt-in real-model Wyoming smoke test (downloads ~252 MB for both
models and exercises English, Hebrew and mixed text), from the repository root:

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
