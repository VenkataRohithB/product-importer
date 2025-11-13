from sqlalchemy import Column, Integer, String, Boolean, Text, Index
from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(255), nullable=False)
    sku_normalized = Column(String(255), nullable=False)
    name = Column(String(512), nullable=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)

    __table_args__ = (
        Index("ix_sku_normalized_unique", "sku_normalized", unique=True),
    )

class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1024), nullable=False)
    event = Column(String(100), nullable=False)  # example: product.imported
    enabled = Column(Boolean, default=True)
