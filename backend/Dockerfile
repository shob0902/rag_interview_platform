# Multi-stage build: compile dependencies (chroma-hnswlib is forced to build
# from source — see requirements.txt) in a stage with a C/C++ toolchain, then
# copy just the installed packages into a slim runtime image.

FROM python:3.11-slim AS builder
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

COPY app ./app
COPY scripts ./scripts
COPY data ./data

# Platforms like Koyeb/Render inject PORT at runtime; default to 8000 for
# `docker run` without one set.
ENV PORT=8000
EXPOSE 8000

# `python -m uvicorn` (rather than the bare `uvicorn` script) guarantees the
# working directory is on sys.path so `app.main` resolves, matching local dev.
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
