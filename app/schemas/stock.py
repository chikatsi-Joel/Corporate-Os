from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StockBase(BaseModel):
    nombre: int
    shareholder_id: str

class StockCreate(StockBase):
    pass

class StockUpdate(BaseModel):
    nombre: Optional[int] = None
    certificat_path: Optional[str] = None

class Stock(StockBase):
    id: str
    date_emission: datetime
    certificat_path: Optional[str] = None

    class Config:
        from_attributes = True

class StockWithShareholder(Stock):
    shareholder_name: str
    shareholder_email: str 