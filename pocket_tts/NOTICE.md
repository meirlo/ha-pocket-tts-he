# Third-party attribution and citations

This repository's original Wyoming wrapper and packaging are licensed under
the [MIT license](LICENSE). Dependencies and downloaded weights retain their
own licenses; the MIT license does not relicense them.

## Speech projects and models

- **Pocket TTS ONNX**, by **thewh1teagle**, is licensed under
  [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/).
  Source: https://github.com/thewh1teagle/pocket-tts-onnx.
  This app installs the unmodified Python package at commit
  `3eaed376097da1ec7ac528309beb683e7ae43c0c` and adds a Wyoming server around it.
  The upstream license is retained in the installed package.
- **Pocket TTS ONNX model**, exported by **thewh1teagle** from Kyutai's Pocket
  TTS, is licensed under **CC BY 4.0** according to its
  [model card](https://huggingface.co/thewh1teagle/pocket-tts-onnx).
  The unmodified `pocket-tts-english-ipa.onnx` (including the Hebrew adapter
  and embedded voices) is downloaded from revision
  `110f5251188e9407b4f724acdd8b0dfd0b20692a`. The model is not included in this
  repository or container image. Keep this attribution and the license link
  with redistributed models or adaptations and indicate any modifications.
- **Kyutai Pocket TTS**, by **Kyutai**, is the original speech synthesis project.
  Source: https://github.com/kyutai-labs/pocket-tts;
  [source license: MIT](https://github.com/kyutai-labs/pocket-tts/blob/main/LICENSE).
  See also the [Pocket TTS technical report](https://kyutai.org/blog/2026-01-13-pocket-tts)
  and [voice catalog](https://huggingface.co/kyutai/tts-voices) for the upstream
  voice recordings, contributors, and recording-specific licenses. The embedded
  voices are supplied by the pinned ONNX model; this app does not add recordings.
- **Wyoming**, by **Michael Hansen and contributors**, is licensed under MIT.
  Source: https://github.com/OHF-voice/wyoming (formerly rhasspy/wyoming).
- **renikud-onnx**, by **thewh1teagle**, is an upstream package dependency
  licensed under CC BY 4.0. Source: https://github.com/thewh1teagle/renikud.
- **ReNikud Hebrew G2P model**, by **Maxim Melichov, Yakov Kolani and Morris Alper**,
  is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Source/model card: https://huggingface.co/renikud/renikud.
  The unmodified `model.onnx` is downloaded from revision
  `a59c632c8cbac0f8c63f298cad77ef3a3a2547c9` for Hebrew synthesis and is not
  bundled in this repository or image. Preserve attribution and indicate
  modifications when redistributing it.

Research citation supplied by the pinned ReNikud model card:

> Melichov, Maxim; Kolani, Yakov; and Alper, Morris (2026).
> *ReNikud: Audio-Supervised Hebrew Grapheme-to-Phoneme Conversion*.
> [Model card and upstream citation](https://huggingface.co/renikud/renikud/blob/a59c632c8cbac0f8c63f298cad77ef3a3a2547c9/README.md).

## Python runtime dependencies

The following credits cover every package in the universal
[`requirements.txt`](requirements.txt) lockfile, including platform-conditional
entries. Version pins are maintained in that file rather than duplicated here.
Project links credit the respective authors and contributors and identify their
source repositories. Licenses are taken from package metadata or upstream
license files; bundled components may have additional notices.

| Package / project | Source citation | License |
| --- | --- | --- |
| `anyio` | [AnyIO](https://github.com/agronholm/anyio) | MIT |
| `attrs` | [attrs](https://github.com/python-attrs/attrs) | MIT |
| `click` | [Pallets Click](https://github.com/pallets/click) | BSD-3-Clause |
| `cloudpickle` | [Cloudpickle](https://github.com/cloudpipe/cloudpickle) | BSD |
| `colorama` | [Colorama](https://github.com/tartley/colorama) | BSD; Windows-only lock entry |
| `dlinfo` | [python-dlinfo](https://github.com/fphammerle/python-dlinfo) | MIT |
| `espeakng-loader` | [eSpeak NG loader](https://github.com/thewh1teagle/espeakng-loader) | MIT loader; bundled eSpeak NG is GPL-3.0-or-later |
| eSpeak NG (bundled library) | [eSpeak NG](https://github.com/espeak-ng/espeak-ng) | GPL-3.0-or-later |
| `filelock` | [Filelock](https://github.com/tox-dev/filelock) | MIT |
| `flatbuffers` | [Google FlatBuffers](https://github.com/google/flatbuffers) | Apache-2.0 |
| `fsspec` | [Filesystem Spec](https://github.com/fsspec/filesystem_spec) | BSD-3-Clause |
| `h11` | [h11](https://github.com/python-hyper/h11) | MIT |
| `heb-tts-normalizer` | [Hebrew TTS normalizer](https://github.com/thewh1teagle/heb-tts-normalizer) | MIT |
| `hf-xet` | [Hugging Face Xet](https://github.com/huggingface/xet-core) | Apache-2.0 |
| `httpcore2` | [HTTPX2 / HTTPCore2](https://github.com/pydantic/httpx2) | BSD-3-Clause |
| `httpx2` | [HTTPX2](https://github.com/pydantic/httpx2) | BSD-3-Clause |
| `httpx2-jsfetch` | [HTTPX2 JSFetch package](https://pypi.org/project/httpx2-jsfetch/) | See package notices; Emscripten-only, not installed in this app's Linux image |
| `huggingface-hub` | [Hugging Face Hub Python library](https://github.com/huggingface/huggingface_hub) | Apache-2.0 |
| `idna` | [IDNA](https://github.com/kjd/idna) | BSD-3-Clause |
| `joblib` | [Joblib](https://github.com/joblib/joblib) | BSD-3-Clause |
| `numpy` | [NumPy](https://github.com/numpy/numpy) | BSD-3-Clause; bundled components also declare 0BSD, MIT, Zlib, and CC0-1.0 |
| `onnxruntime` | [Microsoft ONNX Runtime](https://github.com/microsoft/onnxruntime) | MIT |
| `packaging` | [PyPA Packaging](https://github.com/pypa/packaging) | Apache-2.0 OR BSD-2-Clause |
| `phonemizer` | [Phonemizer](https://github.com/bootphon/phonemizer) | GPL-3.0-or-later |
| `pocket-tts-onnx` | [Pocket TTS ONNX](https://github.com/thewh1teagle/pocket-tts-onnx) | CC-BY-4.0; pinned code/model details above |
| `protobuf` | [Google Protocol Buffers](https://github.com/protocolbuffers/protobuf) | BSD-3-Clause |
| `pyyaml` | [PyYAML](https://github.com/yaml/pyyaml) | MIT |
| `renikud-onnx` | [ReNikud ONNX](https://github.com/thewh1teagle/renikud) | CC-BY-4.0; pinned model details above |
| `sentencepiece` | [Google SentencePiece](https://github.com/google/sentencepiece) | Apache-2.0 |
| `tqdm` | [tqdm](https://github.com/tqdm/tqdm) | MPL-2.0 AND MIT |
| `truststore` | [Truststore](https://github.com/sethmlarson/truststore) | MIT |
| `typing-extensions` | [Python typing extensions](https://github.com/python/typing_extensions) | PSF-2.0 |
| `wyoming` | [Wyoming](https://github.com/OHF-voice/wyoming) | MIT |

## Home Assistant, container, and development projects

These projects provide the host integration, runtime, packaging, or validation
tools. They are not additional speech models. Each retains its own license and
third-party notices.

| Project | Contribution |
| --- | --- |
| [Home Assistant Core](https://github.com/home-assistant/core) | Wyoming integration and voice-assistant configuration. |
| [Home Assistant Supervisor](https://github.com/home-assistant/supervisor) | App lifecycle, persistent data, and Wyoming discovery. |
| [Home Assistant Frontend](https://github.com/home-assistant/frontend) | App store and configuration UI. |
| [My Home Assistant](https://github.com/home-assistant/my.home-assistant.io) | Official repository/app redirect links and button artwork. |
| [Python / CPython](https://github.com/python/cpython) | Python 3.13 runtime and standard-library HTTP, concurrency, and audio-service support. |
| [Docker Official Python Image](https://github.com/docker-library/python) | `python:3.13-slim-bookworm` base image. |
| [Debian](https://www.debian.org/) | Bookworm operating-system packages and system libraries. |
| [GCC / libgomp](https://gcc.gnu.org/onlinedocs/libgomp/) | ONNX Runtime OpenMP support; GPLv3 with the [GCC Runtime Library Exception](https://www.gnu.org/licenses/gcc-exception-3.1.html). |
| [pip](https://github.com/pypa/pip) and [PyPI / Warehouse](https://github.com/pypi/warehouse) | Dependency installation and Python package distribution. |
| [uv](https://github.com/astral-sh/uv) | Dependency locking and local environment tooling. |
| [Docker Buildx](https://github.com/docker/buildx) and [BuildKit](https://github.com/moby/buildkit) | Container builds, including the CI architecture matrix. |
| [QEMU](https://www.qemu.org/) | arm64 emulation in container CI. |
| [actions/checkout](https://github.com/actions/checkout) | GitHub Actions repository checkout. |
| [actions/setup-python](https://github.com/actions/setup-python) | GitHub Actions Python setup. |
| [docker/setup-qemu-action](https://github.com/docker/setup-qemu-action) | GitHub Actions architecture emulation setup. |
| [docker/setup-buildx-action](https://github.com/docker/setup-buildx-action) | GitHub Actions container builder setup. |
| [docker/build-push-action](https://github.com/docker/build-push-action) | GitHub Actions container build validation. |

Development dependencies from [`requirements-dev.txt`](../requirements-dev.txt)
and their additional installed dependencies are credited below. Shared
dependencies such as PyYAML, Packaging, Colorama, and typing extensions are
already listed in the runtime table.

| Package / project | Source citation | License |
| --- | --- | --- |
| `pytest` | [pytest](https://github.com/pytest-dev/pytest) | MIT |
| `pytest-asyncio` | [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio) | Apache-2.0 |
| `ruff` | [Ruff](https://github.com/astral-sh/ruff) | MIT |
| `mypy` | [mypy](https://github.com/python/mypy) | MIT |
| `iniconfig` | [iniconfig](https://github.com/pytest-dev/iniconfig) | MIT |
| `pluggy` | [Pluggy](https://github.com/pytest-dev/pluggy) | MIT |
| `pygments` | [Pygments](https://github.com/pygments/pygments) | BSD-2-Clause |
| `mypy-extensions` | [mypy extensions](https://github.com/python/mypy_extensions) | MIT |
| `pathspec` | [Pathspec](https://github.com/cpburnz/python-pathspec) | MPL-2.0 |
| `librt` | [mypyc runtime](https://github.com/mypyc/librt) | MIT |

## Distribution obligations and compatibility

Dependency license files are retained by normal package installation. The base
image also carries operating-system package notices, generally under
`/usr/share/doc`, and Python's bundled third-party notices. Source repositories
above and PyPI source distributions identify corresponding upstream sources.
When distributing a built container, also satisfy applicable GPL source-provision
obligations for the actual versions and binaries distributed, including eSpeak NG
and Phonemizer. This notice alone is not a substitute for providing source.

The latest Pocket TTS ONNX commit at implementation time requires
`conikud-onnx`, whose repository declares no license. We deliberately pin the
last compatible commit before that dependency was added rather than
redistributing an unlicensed dependency or ignoring package dependencies.

Nakdimon and `conikud-onnx` are not installed or used by this app.

No endorsement by upstream authors is implied. Use generated speech
responsibly; do not impersonate people or imply recordings are authentic.
