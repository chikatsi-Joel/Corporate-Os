from sqlalchemy.orm import Session
from app.database.stock import Stock
from app.schemas.stock import StockCreate, StockUpdate
from typing import List, Optional
from sqlalchemy import func



def get_stock(db: Session, stock_id: str) -> Optional[Stock]:
    return db.query(Stock).filter(Stock.id == stock_id).first()

def get_stocks(db: Session, skip: int = 0, limit: int = 100) -> List[Stock]:
    return db.query(Stock).offset(skip).limit(limit).all()

def get_stocks_by_shareholder(db: Session, shareholder_id: str, skip: int = 0, limit: int = 100) -> List[Stock]:
    return db.query(Stock).filter(Stock.shareholder_id == shareholder_id).offset(skip).limit(limit).all()

def create_stock(db: Session, stock: StockCreate) -> Stock:
    db_stock = Stock(**stock.dict())
    db.add(db_stock)
    db.commit()
    db.refresh(db_stock)
    return db_stock

def update_stock(db: Session, stock_id: str, stock: StockUpdate) -> Optional[Stock]:
    db_stock = get_stock(db, stock_id)
    if db_stock:
        update_data = stock.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_stock, field, value)
        db.commit()
        db.refresh(db_stock)
    return db_stock

def get_total_stocks_by_shareholder(db: Session, shareholder_id: str) -> int:
    result = db.query(func.sum(Stock.nombre)).filter(Stock.shareholder_id == shareholder_id).scalar()
    return result or 0

def get_total_stocks(db: Session) -> int:
    result = db.query(func.sum(Stock.nombre)).scalar()
    return result or 0

def get_stocks_with_shareholder_info(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Stock).join(Stock.shareholder).join(Stock.shareholder.user).offset(skip).limit(limit).all() 