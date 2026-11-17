# Using Pocket TTS

For installation and the official Home Assistant shortcut buttons, see the
[repository README](https://github.com/meirlo/ha-pocket-tts-he#install-the-app).
Add `https://github.com/meirlo/ha-pocket-tts-he.git` to the app store's
**Repositories** dialog, install **Pocket TTS**, and start it. For local installation,
copy its `pocket_tts` folder into `/addons/pocket_tts`, reload the app store,
and install **Pocket TTS** under **Local apps**.

After the app starts, confirm the discovered **Pocket TTS** Wyoming integration
under **Settings > Devices & services**. Then choose Pocket TTS in your English
or Hebrew voice assistant's text-to-speech settings. No web UI is provided.

Supervisor discovery is published only after the model and Wyoming listener are
ready. It uses the app's internal hostname and port `10200`, not the mapped LAN
port; no extra API permissions or mDNS are needed. Standalone servers are not
automatically discovered. Manual **Wyoming Protocol** setup using your server's
LAN IP and mapped port remains supported.

If an existing manual integration already works, ignore a new discovery card
or remove the manual entry before confirming the discovered one to avoid
duplicate TTS entities. Updating to 0.4.0 requires rebuilding/restarting the app
with its updated `config.yaml`.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `voice` | `alba` | Default embedded voice. Home Assistant's per-request voice selection overrides it. |
| `num_threads` | `2` | CPU inference threads, from 1 to 32. More threads are not always faster. |
| `max_text_length` | `4000` | Maximum characters per request, from 1 to 16000. Longer requests are rejected with a Wyoming error. |
| `log_level` | `info` | `debug`, `info`, `warning` or `error`. |

The verified pinned model embeds English voices `alba`, `anna`, `cosette`,
`javert`, `marius`, `michael` and Hebrew voices **`omer`** and **`liat`**
(the upstream model card's voice list is outdated). Voices and their languages
are read from the model itself and advertised to Home Assistant.
An unknown configured voice prevents startup; an unknown requested voice
produces an error instead of silently choosing a substitute.
Change `voice` to another advertised name and restart to change the default.
For Hebrew, select `omer` or `liat` in Home Assistant, or configure one as the
default. English voices use the original text frontend; Hebrew voices use
the IPA adapter. A language-only Wyoming request selects a matching voice
if the configured default has another language. An explicitly selected
voice must match the requested language.

Example app options:

```yaml
voice: alba
num_threads: 2
max_text_length: 4000
log_level: info
```

### Unused optional configuration

`model_path` and `renikud_model_path` are optional advanced overrides, hidden
under **Show unused optional configuration** until set. Leave them unset for
automatic downloads and cache-only loading after the first download.

| Option | Meaning |
| --- | --- |
| `model_path` | Absolute path to a compatible local single-file TTS ONNX export, e.g. `/share/pocket-tts/model.onnx`. An English-only export exposes no Hebrew voices. |
| `renikud_model_path` | Absolute path to a local Renikud ONNX file, e.g. `/share/pocket-tts/renikud.onnx`. Only used when the TTS model includes Hebrew voices. |

Upgraded installations may still have empty path values saved. Remove those
empty keys in the configuration's YAML editor to return them to the unused
optional section. Keep any paths you deliberately configured.

## Speech and local models

English and Hebrew plain-text synthesis are exposed. Hebrew text is normalized
(including numbers, dates and times), and unvocalized Hebrew is converted to
phonemes with Renikud. Mixed Hebrew/English text is supported through the
upstream phonemizer; Latin words in Hebrew requests use eSpeak. Vocalized
Hebrew and upstream `[[IPA]]` pronunciation hints are also supported.

A local TTS model must use the same self-contained format/API as the pinned
upstream revision. Hebrew voices require embedded language metadata and the
IPA adapter with two decode steps. Arbitrary ONNX graphs, split web-demo
assets and voice prompt files are not supported.

Inference is serialized across clients to protect model state. Audio is
sent as it is generated, without buffering the entire utterance. Metadata
requests remain responsive while inference runs. A client that stops
reading is disconnected after 30 seconds of socket backpressure.
An inference failure ends with a Wyoming error, not a successful audio-stop.

## Offline use and backups

The downloaded TTS and Renikud models are cached in `/data/huggingface`, surviving
restarts and upgrades. Every startup first checks the pinned files locally,
without contacting Hugging Face. Only missing files are downloaded; once both
are cached, startup and speech work without internet access. There is no
`offline` switch. Older options files containing a boolean `offline` value are
accepted with a warning; that value no longer changes model loading.
Remove an old `offline` key from saved app options to clear Supervisor's
unknown-option warning after upgrading.

Downloaded cache files are excluded from Home Assistant backups because
they can be downloaded again. Restoring a backup therefore requires
internet access to download missing files, or separately provided local models.
For permanently disconnected systems, copy the pinned
`pocket-tts-english-ipa.onnx` to `/share/pocket-tts/model.onnx` and Renikud's
`model.onnx` to `/share/pocket-tts/renikud.onnx`. Set `model_path` and
`renikud_model_path` accordingly. The shared folder is mounted read-only; back up
your custom model separately. Uploaded/custom models are never deleted
or replaced by this app.

Upgrading from 0.1.0 requires downloading the IPA model and Renikud, even if
the previous English-only model was cached. Missing files download automatically,
or you can provide both files locally. A local English-only model still works offline
without Renikud, but cannot provide Hebrew voices.

The first download needs access to Hugging Face and its download/CDN hosts.
No text or generated audio is sent to Hugging Face; only model artifacts
are fetched. No API key is required for the pinned public model.

## Troubleshooting

- **App not listed:** check that the repository above is added and reload the
  app store. Only 64-bit amd64/aarch64 are supported. For local installation,
  ensure `config.yaml`, `Dockerfile`, `requirements.txt` and `wyoming_pocket_tts`
  are directly inside `/addons/pocket_tts`.
- **Install/build failed:** inspect the build log for GitHub/PyPI/Docker Hub
  connectivity errors, storage shortages or incompatible wheels. The image
  uses Debian and Python 3.13, not the Home Assistant Alpine base.
- **Download/startup failed:** inspect the log, check free disk/RAM and
  connectivity when files are missing, and verify any configured local model paths.
  Download failures stop startup with an error; the TCP socket opens
  only after the model has loaded.
- **Port already in use:** Piper may use the same host port. Change Pocket
  TTS's host port in Network settings, then use that port in the integration.
- **Cannot connect:** wait for `Model ready`, use the LAN IP rather than
  `localhost` for manual setup, and check the port mapping/firewall.
- **No discovery card:** check for `Published Wyoming discovery to Home Assistant`
  in the app log. Discovery failures are logged and retried five times without
  stopping TTS. Check the updated app configuration, restart to retry, or connect
  manually. An already configured or ignored discovery may not show another card.
- **No provider/voice:** reconnect/reload the Wyoming integration after
  changing a local model or upgrading. Choose English for English voices or
  Hebrew for `omer`/`liat`; an English-only custom model cannot expose Hebrew.
- **Slow speech:** try two inference threads, shorter text, and fewer
  competing CPU-heavy apps. CPU performance must be measured on your device.

The TCP watchdog checks listener availability, not synthesis quality.
Never expose this unauthenticated service outside your trusted network.

## Attribution

Pocket TTS ONNX and its model are by thewh1teagle, based on Kyutai's Pocket
TTS, and are used under CC BY 4.0. ReNikud provides Hebrew pronunciation;
Wyoming connects the app to Home Assistant. See [NOTICE](NOTICE.md) for complete
project citations, model authors and revisions, dependency licenses, and
distribution obligations.
