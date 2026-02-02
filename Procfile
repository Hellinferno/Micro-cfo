web: gunicorn src.integration_server:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT
worker: celery -A src.celery_app worker --loglevel=info
