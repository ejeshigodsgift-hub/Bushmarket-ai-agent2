from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_task_lifecycle import AgentTaskLifecycle
from app.services.agent_permission_service import (
    agent_permission_service
)

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)


# =========================================
# GET TASKS
# =========================================
@router.get("/tasks")
async def get_tasks(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    # Placeholder (later: repository fetch with filters/pagination)
    return {
        "tasks": []
    }


# =========================================
# START TASK
# =========================================
@router.post("/task/{task_id}/start")
async def start_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    lifecycle = AgentTaskLifecycle()

    task = await lifecycle.update_status(
        db=db,
        task_id=task_id,
        new_status="in_progress"
    )

    return {
        "task_id": task.id,
        "status": task.status
    }


# =========================================
# COMPLETE TASK (UoW + OUTBOX SAFE)
# =========================================
@router.post("/task/{task_id}/complete")
async def complete_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    await agent_permission_service.require_agent(
        db,
        request.state.user["id"]
    )

    lifecycle = AgentTaskLifecycle()

    task = await lifecycle.update_status(
        db=db,
        task_id=task_id,
        new_status="completed"
    )

    return {
        "task_id": task.id,
        "status": task.status
    }