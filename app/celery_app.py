# app/celery_app.py
from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

BROKER_URL = os.getenv("CELERY_BROKER_URL")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND")

celery_app = Celery(
    "worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

# This ensures Celery finds tasks inside app/
celery_app.autodiscover_tasks(["app"])
