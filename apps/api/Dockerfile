FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY apps/api/pyproject.toml apps/api/pyproject.toml
COPY apps/api/app apps/api/app
COPY apps/api/migrations apps/api/migrations
COPY apps/api/scripts apps/api/scripts
COPY data/seed data/seed

RUN pip install --no-cache-dir -e apps/api

CMD ["python", "apps/api/scripts/start_compose_api.py"]
