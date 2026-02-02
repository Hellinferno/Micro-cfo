web: uvicorn src.integration_server:app --host 0.0.0.0 --port ${PORT:-8000}
worker: celery -A src.celery_app worker --loglevel=info
