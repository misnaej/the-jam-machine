# CPU-only image — works on amd64 and arm64 (no GPU required)
FROM python:3.11-slim

# FluidSynth for audio synthesis — library only, no GUI
RUN apt-get update \
    && apt-get install -y --no-install-recommends libfluidsynth3 git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

# CPU-only torch (~200MB vs ~2GB with CUDA) — sufficient for inference
RUN pip install --no-cache-dir --timeout 300 \
    torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --timeout 300 .

EXPOSE 7860

CMD ["python", "-c", "from jammy.app.playground import demo; demo.launch(server_name='0.0.0.0', server_port=7860)"]
