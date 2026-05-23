from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.agent_task_service import AgentTaskService
from app.services.permission_service import PermissionService


router = APIRouter(prefix="/admin")

permission_service = PermissionService()


# =========================
# ADMIN DASHBOARD
# =========================
@router.get("/dashboard")
def admin_dashboard(request: Request):

    user = request.state.user

    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    roles = user.get("roles", [])

    permission_service.validate_permission(roles, "admin_access")

    return {
        "message": "Admin dashboard",
        "user_id": user.get("id")
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

    if not admin_user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    roles = admin_user.get("roles", [])

    # STRICT ADMIN VALIDATION
    permission_service.validate_permission(roles, "*")

    task_service = AgentTaskService()

    task = task_service.create_task(
        db=db,
        admin_user=admin_user,
        agent_id=payload["agent_id"],
        task_type=payload["task_type"],
        payload=payload.get("payload", {}),
        cooperative_id=payload.get("cooperative_id")
    )

    return {
        "task_id": task.id,
        "status": "assigned"
    }