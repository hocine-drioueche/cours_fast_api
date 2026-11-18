from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_session
from app.models import TaskDB, UserDB
from app.schemas import Task, TaskCreate, TaskUpdate
from app.websocket import manager

router = APIRouter(tags=["tasks"])


@router.get("/tasks", response_model=list[Task])
def get_tasks(
    completed: bool | None = None,
    user_id: int | None = None,
    db: Session = Depends(get_session),
):
    query = db.query(TaskDB)

    if completed is not None:
        query = query.filter(TaskDB.completed == completed)

    if user_id is not None:
        query = query.filter(TaskDB.user_id == user_id)

    return query.all()


@router.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: int, db: Session = Depends(get_session)):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task


@router.post("/tasks", response_model=Task)
async def create_task(
    task: TaskCreate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    if task.user_id is not None:
        user = db.query(UserDB).filter(UserDB.id == task.user_id).first()
        if user is None:
            raise HTTPException(status_code=400, detail="User not found")

    db_task = TaskDB(
        title=task.title,
        completed=task.completed,
        user_id=task.user_id
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    await manager.broadcast({
        "event": "task_created",
        "task": {
            "id": db_task.id,
            "title": db_task.title,
            "completed": db_task.completed,
            "user_id": db_task.user_id
        }
    })

    return db_task


@router.put("/tasks/{task_id}", response_model=Task)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_update.user_id is not None:
        user = db.query(UserDB).filter(UserDB.id == task_update.user_id).first()
        if user is None:
            raise HTTPException(status_code=400, detail="User not found")

    if task_update.title is not None:
        task.title = task_update.title

    if task_update.completed is not None:
        task.completed = task_update.completed

    if task_update.user_id is not None:
        task.user_id = task_update.user_id

    db.commit()
    db.refresh(task)

    await manager.broadcast({
        "event": "task_updated",
        "task": {
            "id": task.id,
            "title": task.title,
            "completed": task.completed,
            "user_id": task.user_id
        }
    })

    return task


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    task_data = {
        "id": task.id,
        "title": task.title,
        "completed": task.completed,
        "user_id": task.user_id
    }

    db.delete(task)
    db.commit()

    await manager.broadcast({
        "event": "task_deleted",
        "task": task_data
    })

    return {"message": f"Task {task_id} deleted"}