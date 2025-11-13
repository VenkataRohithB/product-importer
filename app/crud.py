from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from . import models, schemas

def list_products(db: Session, skip: int, limit: int, filters: dict):
    q = select(models.Product)

    if "sku" in filters:
        q = q.where(models.Product.sku_normalized == filters["sku"].lower())
    if "name" in filters:
        q = q.where(models.Product.name.ilike(f"%{filters['name']}%"))
    if "active" in filters:
        q = q.where(models.Product.active == filters["active"])

    q = q.offset(skip).limit(limit)
    return db.execute(q).scalars().all()

def get_product_by_id(db: Session, pid: int):
    return db.get(models.Product, pid)

def create_product(db: Session, p: schemas.ProductCreate):
    new_product = models.Product(
        sku=p.sku,
        sku_normalized=p.sku.lower(),
        name=p.name,
        description=p.description,
        active=p.active,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

def update_product(db: Session, pid: int, patch: schemas.ProductUpdate):
    product = db.get(models.Product, pid)
    if not product:
        return None

    for field, value in patch.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, pid: int):
    product = db.get(models.Product, pid)
    if not product:
        return False

    db.delete(product)
    db.commit()
    return True

def bulk_delete_all(db: Session):
    db.execute(delete(models.Product))
    db.commit()
