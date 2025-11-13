from pydantic import BaseModel, Field, HttpUrl, AnyUrl
from typing import Optional

class ProductBase(BaseModel):
    sku: str
    name: Optional[str]
    description: Optional[str]
    active: Optional[bool] = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    active: Optional[bool]

class ProductOut(ProductBase):
    id: int
    class Config:
        orm_mode = True

class WebhookBase(BaseModel):
    url: HttpUrl
    event: str
    enabled: Optional[bool] = True

class WebhookCreate(WebhookBase):
    pass

class WebhookOut(WebhookBase):
    id: int
    class Config:
        orm_mode = True

class WebhookUpdate(BaseModel):
    url: AnyUrl
    event: str
    enabled: bool
