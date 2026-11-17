# Third-party attribution

This repository's original Wyoming wrapper and packaging are licensed under
the [MIT license](LICENSE). Dependencies and downloaded weights retain their
own licenses; the MIT license does not relicense them.

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
- **Wyoming**, by **Michael Hansen and contributors**, is licensed under MIT.
  Source: https://github.com/rhasspy/wyoming.
- **renikud-onnx**, by **thewh1teagle**, is an upstream package dependency
  licensed under CC BY 4.0. Source: https://github.com/thewh1teagle/renikud.
- **ReNikud Hebrew G2P model**, by **Maxim Melichov, Yakov Kolani and Morris Alper**,
  is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
  Source/model card: https://huggingface.co/renikud/renikud.
  The unmodified `model.onnx` is downloaded from revision
  `a59c632c8cbac0f8c63f298cad77ef3a3a2547c9` for Hebrew synthesis and is not
  bundled in this repository or image. Preserve attribution and indicate
  modifications when redistributing it.

Other installed dependencies include ONNX Runtime (MIT), NumPy and
SentencePiece (BSD/Apache-2.0 respectively), Hugging Face Hub (Apache-2.0),
phonemizer (GPL-3.0), eSpeak NG / espeakng-loader (GPL-3.0), and
heb-tts-normalizer (MIT). Their license files are retained by normal package
installation. Corresponding sources for these dependencies are available
through their package metadata and source distributions on PyPI. When
distributing a built container, also satisfy applicable GPL source-provision
obligations; this notice alone is not a substitute for providing source.

The latest Pocket TTS ONNX commit at implementation time requires
`conikud-onnx`, whose repository declares no license. We deliberately pin the
last compatible commit before that dependency was added rather than
redistributing an unlicensed dependency or ignoring package dependencies.

No endorsement by upstream authors is implied. Use generated speech
responsibly; do not impersonate people or imply recordings are authentic.
