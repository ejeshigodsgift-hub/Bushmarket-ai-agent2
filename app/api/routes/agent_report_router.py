from fastapi import APIRouter, Depends, Request, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_field_report_service import AgentFieldReportService
from app.services.agent_permission_service import agent_permission_service


router = APIRouter(
    prefix="/agent/reports",
    tags=["Agent Reports"]
)

service = AgentFieldReportService()


# =========================================
# SUBMIT REPORT
# =========================================
@router.post("/submit")
async def submit_report(
    payload: dict,
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    agent_id = request.state.user["id"]

    report = await service.submit_report(
        db=db,
        agent_id=agent_id,
        report_type=payload.get("report_type"),
        report_data=payload.get("report_data"),
        images=payload.get("images", []),
        cooperative_id=payload.get("cooperative_id"),
        location=payload.get("location"),
        title=payload.get("title")
    )

    return {
        "id": report.id,
        "report_type": report.report_type,
        "images_count": len(report.images or []),
        "created_at": report.created_at
    }


# =========================================
# GET MY REPORTS
# =========================================
@router.get("/me")
async def get_my_reports(
    request: Request,
    db: AsyncSession = Depends(get_db)
):

    if not request.state.user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    agent_id = request.state.user["id"]

    await agent_permission_service.require_agent(
        db=db,
        user_id=agent_id
    )

    return {
        "reports": []
    }