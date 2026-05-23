from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent_task_lifecycle import AgentTaskLifecycle


router = APIRouter(prefix="/agent")


# ======================
# LIST TASKS (DASHBOARD)
# ======================
@router.get("/tasks")
def get_tasks():
    return {"tasks": []}


# ======================
# START TASK
# ======================
@router.post("/task/{task_id}/start")
def start_task(task_id: str, request: Request, db: Session = Depends(get_db)):

    lifecycle = AgentTaskLifecycle()

    return lifecycle.update_status(db, task_id, "in_progress")


# ======================
# COMPLETE TASK
# ======================
@router.post("/task/{task_id}/complete")
def complete_task(task_id: str, request: Request, db: Session = Depends(get_db)):

    lifecycle = AgentTaskLifecycle()

    return lifecycle.update_status(db, task_id, "completed")