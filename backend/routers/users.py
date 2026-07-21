from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import UserOut
from services.auth_service import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=List[UserOut])
def list_users(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all users except the current user (for share dialog picker)."""
    users = db.query(User).filter(User.id != current_user.id).all()
    return users
