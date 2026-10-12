FROM python:3.12-slim AS project_branding
WORKDIR /workspace
COPY project*.json ./
COPY branding/ ./branding/
COPY scripts/project_identity.py ./scripts/project_identity.py
RUN python scripts/project_identity.py --output /out

FROM node:24-alpine AS frontend_builder

WORKDIR /workspace/src/frontend

COPY src/frontend/package.json src/frontend/package-lock.json ./
RUN npm ci

COPY src/frontend/ ./
COPY --from=project_branding /out/ ./
ARG VITE_PUBLIC_SITE_URL=""
ARG VITE_SITE_DESCRIPTION=""
ARG VITE_PUBLIC_DISCOVERY="false"
ARG VITE_INDEXNOW_KEY=""
ARG VITE_BUY_ME_A_COFFEE_ENABLED="false"
ARG VITE_BUY_ME_A_COFFEE_URL=""
RUN npm run build


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

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --shell /usr/sbin/nologin app \
    && mkdir -p /var/lib/b4fastapi/objects /var/lib/b4fastapi/database /var/lib/celery \
    && chown -R app:app /var/lib/b4fastapi /var/lib/celery

USER 10001:10001

EXPOSE 8000

CMD ["./.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
