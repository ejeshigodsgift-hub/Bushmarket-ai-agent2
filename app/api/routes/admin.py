from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.permission_service import PermissionService
from app.services.agent_task_service import AgentTaskService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

permission_service = PermissionService()


@router.get("/dashboard")
async def admin_dashboard(
    request: Request
):

    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(
        user["roles"],
        "admin_access"
    )

    return {
        "message": "Admin dashboard",
        "user_id": user["id"]
    }


@router.post("/assign-task")
async def assign_task(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    admin_user = request.state.user

    if not admin_user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(
        admin_user["roles"],
        "assign_agent_task"
    )

    task = await AgentTaskService().create_task(
        db=db,
        admin_user=admin_user,
        agent_id=payload["agent_id"],
        task_type=payload["task_type"],
        payload=payload.get("payload", {}),
        cooperative_id=payload.get("cooperative_id")
    )

    return {
        "task_id": task.id,
        "status": task.status
    }