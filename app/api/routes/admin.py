from fastapi import (
    APIRouter,
    Depends,
    Request,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.agent_task import AssignAgentTaskPayload

from app.services.permission_service import PermissionService
from app.services.agent_task_service import AgentTaskService


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

permission_service = PermissionService()


@router.post("/assign-task")
async def assign_task(
    payload: AssignAgentTaskPayload,
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
        agent_id=payload.agent_id,
        task_type=payload.task_type,
        payload=payload.payload,
        cooperative_id=payload.cooperative_id
    )

    return {
        "task_id": task.id,
        "status": task.status
    }