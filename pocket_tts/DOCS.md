# Using Pocket TTS

Connect using Home Assistant's **Wyoming Protocol** integration, your Home
Assistant host's LAN IP and port `10200`. Then choose Pocket TTS in your
English voice assistant's text-to-speech settings. No automatic discovery
or web UI is provided.

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `voice` | `alba` | Default embedded voice. Home Assistant's per-request voice selection overrides it. |
| `model_path` | empty | Download/cache the pinned English model. Or set an absolute path to a local compatible English single-file ONNX export, e.g. `/share/pocket-tts/model.onnx`. |
| `offline` | `false` | With `true`, only load an already-cached download or local model; never attempt a Hub download. |
| `num_threads` | `2` | CPU inference threads, from 1 to 32. More threads are not always faster. |
| `max_text_length` | `4000` | Maximum characters per request, from 1 to 16000. Longer requests are rejected with a Wyoming error. |
| `log_level` | `info` | `debug`, `info`, `warning` or `error`. |

The verified pinned model embeds `alba`, `anna`, `cosette`, `javert`, `marius`
and `michael` (the upstream model card's voice list is outdated). Available
voices are read from the model itself and advertised to Home Assistant.
An unknown configured voice prevents startup; an unknown requested voice
produces an error instead of silently choosing a substitute.
Change `voice` to another advertised name and restart to change the default.

Example app options:

```yaml
voice: alba
model_path: ""
offline: false
num_threads: 2
max_text_length: 4000
log_level: info
```

Only English plain-text synthesis is exposed. A local model must use the
same self-contained format/API as the pinned upstream revision and contain
English voices; arbitrary ONNX graphs, split web-demo assets, IPA/Hebrew
adapters and voice prompt files are not supported.

Inference is serialized across clients to protect model state. Audio is
sent as it is generated, without buffering the entire utterance. Metadata
requests remain responsive while inference runs. A client that stops
reading is disconnected after 30 seconds of socket backpressure.
An inference failure ends with a Wyoming error, not a successful audio-stop.

## Offline use and backups

The downloaded model is cached in `/data/huggingface`, surviving restarts
and upgrades. After a successful first online startup, set `offline: true`
to require cache-only loading. If the cache is missing, startup fails
explicitly; switch offline off to download again.

Downloaded cache files are excluded from Home Assistant backups because
they can be downloaded again. Restoring a backup therefore requires
internet access with `offline: false`, or a separately provided local model.
For permanently disconnected systems, copy the pinned
`pocket-tts-english.onnx` to `/share/pocket-tts/model.onnx` and set
`model_path` accordingly. The shared folder is mounted read-only; back up
your custom model separately. Uploaded/custom models are never deleted
or replaced by this app.

The first download needs access to Hugging Face and its download/CDN hosts.
No text or generated audio is sent to Hugging Face; only model artifacts
are fetched. No API key is required for the pinned public model.

## Troubleshooting

- **App not listed:** ensure `config.yaml`, `Dockerfile`, `requirements.txt`
  and `wyoming_pocket_tts` are directly inside the local `pocket_tts` folder,
  then reload the store. Only 64-bit amd64/aarch64 are supported.
- **Install/build failed:** inspect the build log for GitHub/PyPI/Docker Hub
  connectivity errors, storage shortages or incompatible wheels. The image
  uses Debian and Python 3.13, not the Home Assistant Alpine base.
- **Download/startup failed:** inspect the log, check free disk/RAM and
  connectivity, and verify `offline` and `model_path`. The TCP socket opens
  only after the model has loaded.
- **Port already in use:** Piper may use the same host port. Change Pocket
  TTS's host port in Network settings, then use that port in the integration.
- **Cannot connect:** wait for `Model ready`, use the LAN IP rather than
  `localhost` in Home Assistant, and check the port mapping/firewall.
- **No provider/voice:** reconnect/reload the Wyoming integration after
  changing a local model. Ensure the assistant's language is English.
- **Slow speech:** try two inference threads, shorter text, and fewer
  competing CPU-heavy apps. CPU performance must be measured on your device.

The TCP watchdog checks listener availability, not synthesis quality.
Never expose this unauthenticated service outside your trusted network.

## Attribution

Pocket TTS ONNX and its model are by thewh1teagle, based on Kyutai's Pocket
TTS, and are used under CC BY 4.0. See [NOTICE](NOTICE.md) for source links,
revisions, license details and distribution obligations.
