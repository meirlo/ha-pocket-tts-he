# Changelog

## 0.4.0

- Always load cached models without network access; download only missing pinned files.
- Remove the `offline` switch; accept legacy boolean options with a migration warning.
- Move local TTS and Renikud model paths under unused optional configuration.
- Add complete project citations and public repository installation shortcuts.

## 0.3.0

- Publish Wyoming discovery through Supervisor once the TTS listener is ready.
- Offer a Home Assistant discovered-integration confirmation without host/port entry.
- Keep standalone/manual connections working; discovery failures are logged and retried.

## 0.2.0

- Add Hebrew voices `omer` and `liat` alongside the existing English voices.
- Normalize Hebrew and mixed English/Hebrew text and synthesize through the IPA adapter.
- Pin and persist the Renikud G2P model, with offline and local-model support.
- Advertise per-voice languages and validate/select voices for English and Hebrew requests.
- Upgrading downloads the IPA model and Renikud; English-only offline caches need an online
  startup or locally supplied models.

## 0.1.0

- Initial English Pocket TTS ONNX Wyoming service and Home Assistant app.
- Embedded voice discovery, streaming PCM audio, serialized CPU inference.
- Pinned dependencies/model, persistent cache and offline/local-model options.
