# app/tasks.py
import os
import csv
import time
import requests
from celery import shared_task
from sqlalchemy import text, create_engine
from dotenv import load_dotenv
from .utils.progress import set_progress
from .database import Base
from . import models
from app.celery_app import celery_app

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)

BATCH_SIZE = 1000

@celery_app.task(bind=True)
def import_csv_task(self, csv_path: str, task_id: str):
    Base.metadata.create_all(bind=engine)

    total = sum(1 for _ in open(csv_path, "r", encoding="utf-8", errors="ignore"))
    if total == 0:
        set_progress(task_id, 100, "No rows")
        return {"status": "empty"}

    processed = 0
    conn = engine.connect()

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        batch = []

        for row in reader:
            sku = (row.get("sku") or row.get("SKU") or "").strip()
            if not sku:
                continue

            batch.append({
                "sku": sku,
                "sku_normalized": sku.lower(),
                "name": row.get("name") or "",
                "description": row.get("description") or "",
                "active": True
            })

            if len(batch) == BATCH_SIZE:
                _upsert_batch(conn, batch)
                processed += len(batch)
                batch.clear()
                pct = int(processed / total * 100)
                set_progress(task_id, pct, f"Processed {processed}/{total}")

        if batch:
            _upsert_batch(conn, batch)
            processed += len(batch)
            pct = int(processed / total * 100)
            set_progress(task_id, pct, f"Processed {processed}/{total}")

    conn.close()
    set_progress(task_id, 100, "Completed")
    return {"processed": processed, "status": "done"}


def _upsert_batch(conn, batch):
    values = []
    params = {}

    for i, r in enumerate(batch):
        values.append(f"(:sku{i}, :norm{i}, :name{i}, :desc{i}, :active{i})")
        params[f"sku{i}"] = r["sku"]
        params[f"norm{i}"] = r["sku_normalized"]
        params[f"name{i}"] = r["name"]
        params[f"desc{i}"] = r["description"]
        params[f"active{i}"] = r["active"]

    sql = f"""
        INSERT INTO products (sku, sku_normalized, name, description, active)
        VALUES {','.join(values)}
        ON CONFLICT (sku_normalized)
        DO UPDATE SET
            sku = EXCLUDED.sku,
            name = EXCLUDED.name,
            description = EXCLUDED.description,
            active = EXCLUDED.active;
    """

    conn.execute(text(sql), params)
    conn.commit()


@celery_app.task
def test_webhook_task(wid, url, event):
    start = time.time()
    try:
        res = requests.post(url, json={"test": True, "event": event})
        duration = round((time.time() - start) * 1000, 2)
        return {"status_code": res.status_code, "response_ms": duration}
    except Exception as e:
        return {"error": str(e), "status": "failed"}
