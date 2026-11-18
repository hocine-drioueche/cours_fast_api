from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import UserDB
from app.routers.auth import router as auth_router
from app.routers.tasks import router as tasks_router
from app.routers.ws import router as ws_router
from app.routers.users import router as users_router  # ← NOUVEAU

app = FastAPI()

Base.metadata.create_all(bind=engine)


def seed_data():
    db: Session = SessionLocal()

    user_count = db.query(UserDB).count()
    if user_count == 0:
        db.add_all([
            UserDB(username="alice"),
            UserDB(username="bob"),
        ])
        db.commit()

    db.close()


seed_data()

app.include_router(auth_router)
app.include_router(tasks_router)
app.include_router(ws_router)
app.include_router(users_router)  # ← NOUVEAU