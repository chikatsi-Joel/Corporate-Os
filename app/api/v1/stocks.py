from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.crud.stock_repository import (
    get_stocks, get_stock, create_stock, get_stocks_by_shareholder,
    get_total_stocks_by_shareholder, get_total_stocks
)
from app.crud.user_repository import get_user
from app.schemas.stock import Stock, StockCreate, StockWithShareholder
from app.api.deps import get_current_admin, get_current_shareholder, get_current_user
from app.core.role import Role

router = APIRouter()

@router.get("/", response_model=List[Stock])
def read_stocks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    stocks = get_stocks(db, skip=skip, limit=limit)
    return stocks

@router.post("/", response_model=Stock)
def create_new_stock(
    stock: StockCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    shareholder = get_user(db, stock.shareholder_id)
    if not shareholder or shareholder.role != Role.ACTIONNAIRE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Shareholder not found"
        )
    
    return create_stock(db=db, stock=stock)

@router.get("/my-stocks", response_model=List[Stock])
def read_my_stocks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_shareholder)
):
    stocks = get_stocks_by_shareholder(db, current_user.id, skip=skip, limit=limit)
    return stocks

@router.get("/my-total")
def read_my_total_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_shareholder)
):
    total = get_total_stocks_by_shareholder(db, current_user.id)
    return {"total_stocks": total}

@router.get("/total")
def read_total_stocks(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    total = get_total_stocks(db)
    return {"total_stocks": total}

@router.get("/{stock_id}", response_model=Stock)
def read_stock(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    stock = get_stock(db, stock_id=stock_id)
    if stock is None:
        raise HTTPException(status_code=404, detail="Stock not found")
    
    if current_user.role == Role.ACTIONNAIRE and stock.shareholder_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return stock 