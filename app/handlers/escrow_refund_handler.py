from sqlalchemy import select

from app.db.models.escrow_transaction import EscrowTransaction

from app.services.notification_service import (
    notification_service
)

from app.services.audit_service import AuditService


class EscrowRefundHandler:

    def __init__(self):
        self.audit = AuditService()

    async def handle(
        self,
        db,
        event
    ):

        payload = event["payload"]

        escrow_id = payload.get("escrow_id")

        if not escrow_id:
            return

        stmt = (
            select(EscrowTransaction)
            .where(
                EscrowTransaction.id == escrow_id
            )
            .limit(1)
        )

        result = await db.execute(stmt)

        escrow = result.scalar_one_or_none()

        if not escrow:
            return

        # ===================================
        # UPDATE ESCROW STATUS
        # ===================================
        escrow.status = "refunded"

        # ===================================
        # NOTIFY USER
        # ===================================
        if getattr(escrow, "buyer_id", None):

            await notification_service.send_email(
                db=db,
                user_id=escrow.buyer_id,
                email=payload.get("buyer_email", ""),
                subject="Escrow Refund Processed",
                message=(
                    f"Your escrow refund for "
                    f"{escrow.reference} "
                    f"has been processed."
                )
            )

        # ===================================
        # AUDIT LOG
        # ===================================
        await self.audit.log(
            db=db,
            user_id=getattr(escrow, "buyer_id", None),
            action="escrow_refund_processed",
            entity_type="escrow",
            entity_id=str(escrow.id)
        )

        await db.flush()