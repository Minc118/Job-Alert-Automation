FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend

COPY README.md .gitignore /app/
COPY backend/pyproject.toml backend/README.md ./
COPY backend/job_alert_automation ./job_alert_automation
COPY backend/api ./api
COPY backend/config ./config
COPY backend/migrations ./migrations
COPY backend/tests ./tests

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]" \
    && mkdir -p /app/secrets /app/output /app/private

CMD ["python", "-m", "job_alert_automation.main", "--help"]
