#!/bin/bash
echo "=== ENV CHECK ==="
echo "DATABASE_URL exists: ${DATABASE_URL:+yes}"
echo "SECRET_KEY exists: ${SECRET_KEY:+yes}"
echo "================="
export PYTHONPATH=/app/src
alembic upgrade head && uvicorn pharmatrack.main:app --host 0.0.0.0 --port $PORT