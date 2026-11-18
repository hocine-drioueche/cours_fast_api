from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_session
from app.models import UserDB
from app.schemas import User

router = APIRouter(tags=["users"])


@router.get("/users", response_model=list[User])
def get_users(db: Session = Depends(get_session)):
    return db.query(UserDB).all()