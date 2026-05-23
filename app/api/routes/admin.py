from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent_task_service import AgentTaskService

router = APIRouter(prefix="/admin")


# =========================
# ADMIN DASHBOARD
# =========================
@router.get("/dashboard")
def admin_dashboard(request: Request):

    user = request.state.user

    if not user:
        return {"error": "Unauthorized"}

    return {
        "message": "Admin dashboard"
    }


# =========================
# ASSIGN AGENT TASK
# =========================
@router.post("/assign-task")
def assign_task(
    payload: dict,
    request: Request,
    db: Session = Depends(get_db)
):

    admin_user = request.state.user

    task_service = AgentTaskService()

    task = task_service.create_task(
        db=db,
        admin_user=admin_user,
        agent_id=payload["agent_id"],
        task_type=payload["task_type"],
        payload=payload.get("payload", {}),
        cooperative_id=payload.get("cooperative_id")
    )

    return {"task_id": task.id}