from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.agent_field_report import AgentFieldReport
from app.services.agent_permission_service import agent_permission_service


class AgentFieldReportService:

    VALID_REPORTS = [
        "supplier_report",
        "product_report",
        "market_price_report",
        "delivery_report"
    ]

    async def submit_report(
        self,
        db: AsyncSession,
        agent_id: str,
        report_type: str,
        report_data: dict,
        cooperative_id: str | None = None,
        location: str | None = None,
        title: str | None = None
    ):

        # =====================================
        # VALIDATE AGENT
        # =====================================
        await agent_permission_service.require_agent(
            db=db,
            user_id=agent_id
        )

        # =====================================
        # VALIDATE REPORT TYPE
        # =====================================
        if report_type not in self.VALID_REPORTS:
            raise ValueError("Invalid report type")

        # =====================================
        # CREATE REPORT
        # =====================================
        report = AgentFieldReport(
            agent_id=agent_id,
            cooperative_id=cooperative_id,
            report_type=report_type,
            report_data=report_data,
            location=location,
            title=title
        )

        db.add(report)
        await db.commit()
        await db.refresh(report)

        return report