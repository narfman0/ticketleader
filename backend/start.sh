#!/bin/sh
poetry install
poetry run alembic upgrade head
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload