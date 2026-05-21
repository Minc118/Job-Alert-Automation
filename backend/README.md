# Job Alert Automation Backend

Python CLI and FastAPI backend for the Job Alert Automation repository.

Run backend commands from this directory:

```bash
cd backend
```

Install the editable backend with development dependencies:

```bash
python -m pip install -e ".[dev]"
```

The default `.env` remains at the repository root. Root-level `secrets/`, `private/`, and `output/` directories remain the runtime file locations.

Run tests:

```bash
python -m pytest
```

Run the CLI:

```bash
python -m job_alert_automation.main --help
python -m job_alert_automation.main --dry-run
python -m job_alert_automation.main --check-db
python -m job_alert_automation.main --migrate
```

Run the FastAPI server:

```bash
uvicorn api.app:app --reload --host 127.0.0.1 --port 8000
```

Docker Compose stays rooted at the repository root:

```bash
docker compose build
docker compose run --rm app python -m pytest
```
