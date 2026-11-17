FROM python:3.13-slim-bookworm

ARG BUILD_ARCH
LABEL io.hass.name="Pocket TTS" \
      io.hass.description="Pocket TTS ONNX over Wyoming" \
      io.hass.type="addon" \
      io.hass.version="0.3.0" \
      io.hass.arch="${BUILD_ARCH}"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HUB_DISABLE_TELEMETRY=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && pip check

COPY wyoming_pocket_tts ./wyoming_pocket_tts
COPY NOTICE.md LICENSE ./
EXPOSE 10200
ENTRYPOINT ["python", "-m", "wyoming_pocket_tts"]
CMD ["--options", "/data/options.json", "--data-dir", "/data"]
