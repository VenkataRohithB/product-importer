import os
import uuid
import shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base
from . import crud, schemas, models
from fastapi import UploadFile, File
from .tasks import import_csv_task, test_webhook_task
from .utils.progress import get_progress

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import SessionLocal, engine, Base

app = FastAPI(title="Product Importer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

UPLOAD_DIR = "/tmp/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# PRODUCT CRUD -------------------------------------------------

@app.post("/products", response_model=schemas.ProductOut)
def create_product(item: schemas.ProductCreate, db: Session = Depends(get_db)):
    return crud.create_product(db, item)

@app.get("/products", response_model=list[schemas.ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 50,
    sku: str | None = Query(None),
    name: str | None = Query(None),
    active: bool | None = Query(None),
    db: Session = Depends(get_db),
):
    filters = {}
    if sku: filters["sku"] = sku
    if name: filters["name"] = name
    if active is not None: filters["active"] = active

    return crud.list_products(db, skip, limit, filters)

@app.get("/products/{pid}", response_model=schemas.ProductOut)
def get_product(pid: int, db: Session = Depends(get_db)):
    product = crud.get_product_by_id(db, pid)
    if not product:
        raise HTTPException(404, "Not found")
    return product

@app.put("/products/{pid}", response_model=schemas.ProductOut)
def update_product(pid: int, patch: schemas.ProductUpdate, db: Session = Depends(get_db)):
    p = crud.update_product(db, pid, patch)
    if not p:
        raise HTTPException(404, "Not found")
    return p

@app.delete("/products/{pid}")
def delete_product(pid: int, db: Session = Depends(get_db)):
    ok = crud.delete_product(db, pid)
    if not ok:
        raise HTTPException(404, "Not found")
    return {"status": "deleted"}

@app.post("/products/delete_all")
def delete_all(db: Session = Depends(get_db)):
    crud.bulk_delete_all(db)
    return {"status": "ok"}

# WEBHOOK CRUD -------------------------------------------------

@app.post("/webhooks", response_model=schemas.WebhookOut)
def create_webhook(item: schemas.WebhookCreate, db: Session = Depends(get_db)):
    w = models.Webhook(url=str(item.url), event=item.event, enabled=item.enabled)
    db.add(w)
    db.commit()
    db.refresh(w)
    return w

@app.get("/webhooks", response_model=list[schemas.WebhookOut])
def list_webhooks(db: Session = Depends(get_db)):
    return db.query(models.Webhook).all()

@app.put("/webhooks/{wid}", response_model=schemas.WebhookOut)
def update_webhook(wid: int, patch: schemas.WebhookUpdate, db: Session = Depends(get_db)):
    w = db.query(models.Webhook).filter(models.Webhook.id == wid).first()
    if not w:
        raise HTTPException(404, "Webhook not found")

    w.url = patch.url
    w.event = patch.event
    w.enabled = patch.enabled
    db.commit()
    db.refresh(w)
    return w

@app.delete("/webhooks/{wid}")
def delete_webhook(wid: int, db: Session = Depends(get_db)):
    w = db.query(models.Webhook).filter(models.Webhook.id == wid).first()
    if not w:
        raise HTTPException(404, "Webhook not found")

    db.delete(w)
    db.commit()
    return {"status": "deleted"}

@app.post("/webhooks/{wid}/test")
def test_webhook(wid: int, db: Session = Depends(get_db)):
    w = db.query(models.Webhook).filter(models.Webhook.id == wid).first()
    if not w:
        raise HTTPException(404, "Webhook not found")

    task_id = test_webhook_task.delay(w.id, w.url, w.event)
    return {"task_id": str(task_id), "status": "triggered"}

# Upload --------------------------------------------------
@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(400, "Only CSV files allowed")

    task_id = str(uuid.uuid4())
    file_path = f"{UPLOAD_DIR}/{task_id}.csv"

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Start Celery background job
    import_csv_task.delay(file_path, task_id)

    return {"task_id": task_id, "status": "started"}

# Progress ------------------------------------------------
@app.get("/progress/{task_id}")
def progress(task_id: str):
    pct, msg = get_progress(task_id)
    return {"progress": pct, "status": msg}
