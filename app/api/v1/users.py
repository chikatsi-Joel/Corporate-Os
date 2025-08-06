from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ...core.permission import permission
from typing import List
from app.db.session import get_db
from app.crud.user_repository import get_users, get_user, create_user, get_shareholders, get_user_by_email
from app.schemas.user import User, UserCreate
from app.api.deps import get_current_admin, get_current_user
from app.core.role import Role

router = APIRouter()

@router.get("/me", response_model=User)
def read_users_me(current_user = Depends(get_current_user)):
    return current_user

@router.get("/", response_model=List[User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    users = get_users(db, skip=skip, limit=limit)
    return users

@router.get("/shareholders", response_model=List[User])
@permission.hasPermission(role="ROLE_ADMIN")
def read_shareholders(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    shareholders = get_shareholders(db, skip=skip, limit=limit)
    return shareholders

@router.post("/", response_model=User)
@permission.hasPermission(role="ROLE_ADMIN")
def create_new_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    return create_user(db=db, user=user)

@router.get("/{user_id}", response_model=User)
@permission.hasPermission(role="ROLE_ACTIONNAIRE")
def read_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    db_user = get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user 