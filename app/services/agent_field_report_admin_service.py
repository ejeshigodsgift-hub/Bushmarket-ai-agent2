from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.db.models.agent_field_report import AgentFieldReport


class AgentFieldReportAdminService:

    async def get_pending_reports(self, db: AsyncSession):
        result = await db.execute(
            select(AgentFieldReport).where(
                AgentFieldReport.status == "pending"
            ).order_by(
                AgentFieldReport.created_at.desc()
            )
        )

        return result.scalars().all()

    async def get_report(self, db: AsyncSession, report_id: str):
        result = await db.execute(
            select(AgentFieldReport).where(
                AgentFieldReport.id == report_id
            )
        )

        report = result.scalar_one_or_none()

        if not report:
            raise HTTPException(404, "Report not found")

        return report

    async def approve_report(self, db: AsyncSession, report_id: str, admin_id: str):

        report = await self.get_report(db, report_id)

        report.status = "approved"

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report

    async def reject_report(self, db: AsyncSession, report_id: str, admin_id: str):

        report = await self.get_report(db, report_id)

        report.status = "rejected"

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report