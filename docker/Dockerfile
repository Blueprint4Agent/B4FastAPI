FROM node:20-alpine AS frontend_builder

WORKDIR /workspace/src/frontend

COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci

COPY src/frontend/ ./
RUN npx tsc && npx vite build


FROM python:3.12-slim AS backend_runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app/src/backend

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY src/backend/pyproject.toml src/backend/uv.lock ./
RUN uv sync --frozen --no-dev

COPY src/backend/ ./
COPY --from=frontend_builder /workspace/src/frontend/dist ./app/static/dist

EXPOSE 8000

CMD ["./.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
