from fastapi import (
    APIRouter,
    Request,
    Depends,
    HTTPException
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.services.agent_task_lifecycle import AgentTaskLifecycle


router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)


@router.get("/tasks")
async def get_tasks():

    return {
        "tasks": []
    }


@router.post("/task/{task_id}/start")
async def start_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    lifecycle = AgentTaskLifecycle()

    return await lifecycle.update_status(
        db,
        task_id,
        "in_progress"
    )


@router.post("/task/{task_id}/complete")
async def complete_task(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(401, "Unauthorized")

    lifecycle = AgentTaskLifecycle()

    return await lifecycle.update_status(
        db,
        task_id,
        "completed"
    )