from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Task, TaskStatus
from .schemas import PaginatedTasks, TaskCreate, TaskOut, TaskUpdate

app = FastAPI(
    title="Tasks API",
    description="RESTful API for managing tasks with CRUD, pagination, and search.",
    version="1.0.0",
)

# CORS: allow React frontend on port 3000. You can extend with env var if needed.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Create database tables if migrations are not used."""
    Base.metadata.create_all(bind=engine)


# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", tags=["Health"])
def health_check():
    """Health check endpoint.

    Returns:
        JSON with a basic health message.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.get(
    "/tasks",
    response_model=PaginatedTasks,
    summary="List tasks with pagination and optional search",
    tags=["Tasks"],
)
def list_tasks(
    page: int = Query(1, ge=1, description="1-based page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    q: Optional[str] = Query(None, description="Optional search by title substring (case-insensitive)"),
    db: Session = Depends(get_db),
):
    """List tasks with pagination and optional case-insensitive title search.

    Parameters:
        page: 1-based page number.
        page_size: number of items per page (1-100).
        q: Optional search string to match title (ILIKE).

    Returns:
        PaginatedTasks: total count, page, page_size, and items.
    """
    stmt = select(Task)
    count_stmt = select(func.count())

    if q:
        ilike_expr = f"%{q}%"
        stmt = stmt.where(Task.title.ilike(ilike_expr))
        count_stmt = count_stmt.select_from(Task).where(Task.title.ilike(ilike_expr))
    else:
        count_stmt = count_stmt.select_from(Task)

    total = db.execute(count_stmt).scalar_one()
    offset = (page - 1) * page_size

    stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(page_size)
    items = db.execute(stmt).scalars().all()

    return PaginatedTasks(total=total, page=page, page_size=page_size, items=items)


# PUBLIC_INTERFACE
@app.post(
    "/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    tags=["Tasks"],
)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    task = Task(
        title=payload.title.strip(),
        description=payload.description,
        status=TaskStatus(payload.status.value),
    )
    now = datetime.now(timezone.utc)
    task.created_at = now
    task.updated_at = now

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# PUBLIC_INTERFACE
@app.get(
    "/tasks/{task_id}",
    response_model=TaskOut,
    summary="Get task by ID",
    tags=["Tasks"],
)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Retrieve a single task by ID."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# PUBLIC_INTERFACE
@app.put(
    "/tasks/{task_id}",
    response_model=TaskOut,
    summary="Update a task completely",
    tags=["Tasks"],
)
def update_task(task_id: int, payload: TaskCreate, db: Session = Depends(get_db)):
    """Replace an existing task with provided data."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    task.title = payload.title.strip()
    task.description = payload.description
    task.status = TaskStatus(payload.status.value)
    task.touch()

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# PUBLIC_INTERFACE
@app.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    tags=["Tasks"],
)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task by ID."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
    return None


# PUBLIC_INTERFACE
@app.patch(
    "/tasks/{task_id}",
    response_model=TaskOut,
    summary="Partially update a task",
    tags=["Tasks"],
)
def patch_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Partially update fields of a task."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.title is not None:
        task.title = payload.title.strip()
    if payload.description is not None:
        task.description = payload.description
    if payload.status is not None:
        task.status = TaskStatus(payload.status.value)
    task.touch()

    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# PUBLIC_INTERFACE
@app.patch(
    "/tasks/{task_id}/toggle",
    response_model=TaskOut,
    summary="Toggle task status",
    description="Flip status: pending -> completed or completed -> pending",
    tags=["Tasks"],
)
def toggle_task_status(task_id: int, db: Session = Depends(get_db)):
    """Toggle a task's status."""
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task.status = TaskStatus.COMPLETED if task.status == TaskStatus.PENDING else TaskStatus.PENDING
    task.touch()
    db.add(task)
    db.commit()
    db.refresh(task)
    return task
