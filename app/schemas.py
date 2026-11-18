from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    completed: bool = False
    user_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    completed: bool | None = None
    user_id: int | None = None


class Task(BaseModel):
    id: int
    title: str
    completed: bool
    user_id: int | None = None


class User(BaseModel):
    id: int
    username: str


class LoginData(BaseModel):
    username: str