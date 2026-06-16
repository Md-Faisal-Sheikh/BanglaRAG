FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    EMBEDDING_PROVIDER=hash \
    VECTOR_STORE=memory \
    AUTO_INGEST_CORPUS=data/corpus \
    LLM_PROVIDER=mock \
    USE_RERANKER=false \
    CORS_ORIGINS=* \
    TOKENIZERS_PARALLELISM=false \
    HF_HOME=/app/.cache/huggingface \
    SENTENCE_TRANSFORMERS_HOME=/app/.cache/sentence-transformers

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-space.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-space.txt

COPY . .

EXPOSE 7860

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860}"]
