FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md .gitignore ./
COPY job_alert_automation ./job_alert_automation
COPY api ./api
COPY config ./config
COPY migrations ./migrations
COPY tests ./tests

RUN python -m pip install --upgrade pip \
    && python -m pip install -e ".[dev]" \
    && mkdir -p /app/secrets /app/output /app/private

CMD ["python", "-m", "job_alert_automation.main", "--help"]
