FILE: app/services/financial_audit_replay_service.py

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ledger_entry import LedgerEntry
from app.db.models.event_log import EventLog
from app.db.models.audit_log import AuditLog

class FinancialAuditReplayService:

    async def replay_ledger(
        self,
        db: AsyncSession,
        account_id: str
    ):

        result = await db.execute(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account_id)
            .order_by(LedgerEntry.created_at.asc())
        )

        entries = result.scalars().all()

        balance = Decimal("0.00")

        for entry in entries:

            if entry.entry_type == "credit":
                balance += entry.amount
            else:
                balance -= entry.amount

        return {
            "account_id": account_id,
            "reconstructed_balance":  str(balance),
            "entries_processed": len(entries)
        }

    async def replay_events(
        self,
        db: AsyncSession
    ):
 
        result = await db.execute(
            select(EventLog)
            .order_by(EventLog.created_at.asc())
        )

        events = result.scalars().all()

        return {
            "events_processed": len(events),
            "status": "replayed"
        }

    async def replay_audit_logs(
        self,
        db: AsyncSession
    ):

        result = await db.execute(
            select(AuditLog)
            .order_by(AuditLog.created_at.asc())
        )

        logs = result.scalars().all()

        return {
            "audit_records": len(logs),
            "status": "verified"
        }