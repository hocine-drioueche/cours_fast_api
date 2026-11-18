from datetime import datetime
from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    completed: bool = False
    user_id: int | None = None
    priority: int = 2  # ← NOUVEAU (défaut 2)

class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None
    user_id: int | None = None
    priority: int | None = None  # ← NOUVEAU (optionnel)

class Task(BaseModel):
    id: int
    title: str
    completed: bool
    user_id: int | None = None
    priority: int  # ← NOUVEAU (obligatoire en lecture)
    created_at: datetime  # ← NOUVEAU (lecture seule)


class User(BaseModel):
    id: int
    username: str


class LoginData(BaseModel):
    username: str