from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent_field_report_admin_service import AgentFieldReportAdminService
from app.services.permission_service import PermissionService

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])

service = AgentFieldReportAdminService()
permission_service = PermissionService()


# =========================
# GET PENDING REPORTS
# =========================
@router.get("/pending")
async def get_pending_reports(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(user.get("roles", []), "review_reports")

    return await service.get_pending_reports(db)


# =========================
# GET SINGLE REPORT
# =========================
@router.get("/{report_id}")
async def get_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(user.get("roles", []), "review_reports")

    return await service.get_report(db, report_id)


# =========================
# APPROVE REPORT
# =========================
@router.post("/{report_id}/approve")
async def approve_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(user.get("roles", []), "review_reports")

    return await service.approve_report(
        db=db,
        report_id=report_id,
        admin_id=user["id"]
    )


# =========================
# REJECT REPORT
# =========================
@router.post("/{report_id}/reject")
async def reject_report(
    report_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    user = request.state.user

    if not user:
        raise HTTPException(401, "Unauthorized")

    permission_service.validate_permission(user.get("roles", []), "review_reports")

    return await service.reject_report(
        db=db,
        report_id=report_id,
        admin_id=user["id"]
    )