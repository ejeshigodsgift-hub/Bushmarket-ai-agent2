from decimal import Decimal
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.ledger_accounts import LedgerAccount
from app.db.models.ledger_entries import LedgerEntry
from fastapi import HTTPException


class LedgerEngine:
    """
    Double-entry accounting engine (CORE FINANCIAL SYSTEM)
    """

    def __init__(self):
        pass

    # =========================================================
    # PUBLIC API: POST ENTRY SET (DOUBLE ENTRY TRANSACTION)
    # =========================================================
    async def post_double_entry(
        self,
        db: AsyncSession,
        reference: str,
        description: str,
        entries: List[Dict],
    ):
        """
        entries format:
        [
            {
                "account_id": "...",
                "debit": Decimal,
                "credit": Decimal
            }
        ]
        """

        self._validate_entries(entries)

        total_debit = Decimal("0")
        total_credit = Decimal("0")

        ledger_rows = []

        for e in entries:
            debit = Decimal(str(e.get("debit", 0)))
            credit = Decimal(str(e.get("credit", 0)))

            total_debit += debit
            total_credit += credit

            if debit > 0:
                ledger_rows.append(
                    LedgerEntry(
                        account_id=e["account_id"],
                        entry_type="debit",
                        amount=debit,
                        reference=reference,
                        description=description
                    )
                )

            if credit > 0:
                ledger_rows.append(
                    LedgerEntry(
                        account_id=e["account_id"],
                        entry_type="credit",
                        amount=credit,
                        reference=reference,
                        description=description
                    )
                )

        # =========================
        # BALANCE CHECK (CRITICAL)
        # =========================
        if total_debit != total_credit:
            raise HTTPException(
                status_code=500,
                detail=f"Unbalanced entry: debit={total_debit}, credit={total_credit}"
            )

        db.add_all(ledger_rows)
        await db.flush()

        return {
            "reference": reference,
            "debit": str(total_debit),
            "credit": str(total_credit),
            "status": "posted"
        }

    # =========================================================
    # RULE ENGINE ENTRY POINT
    # =========================================================
    async def apply_rule(
        self,
        db: AsyncSession,
        rule: str,
        context: dict
    ):
        """
        Converts business events → ledger postings
        """

        if rule == "order_created":
            return await self._rule_order_created(db, context)

        if rule == "escrow_deposit":
            return await self._rule_escrow_deposit(db, context)

        if rule == "refund":
            return await self._rule_refund(db, context)

        raise HTTPException(400, f"Unknown ledger rule: {rule}")

    # =========================================================
    # RULE: ORDER CREATED
    # =========================================================
    async def _rule_order_created(self, db, ctx):

        revenue_account = ctx["revenue_account"]
        escrow_account = ctx["escrow_account"]
        platform_fee_account = ctx["platform_fee_account"]

        amount = Decimal(str(ctx["amount"]))
        fee = Decimal(str(ctx["fee"]))

        return await self.post_double_entry(
            db=db,
            reference=ctx["order_id"],
            description="Order created",
            entries=[
                # Customer pays into escrow
                {
                    "account_id": escrow_account,
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account_id": revenue_account,
                    "debit": 0,
                    "credit": amount
                },
                # Platform fee
                {
                    "account_id": platform_fee_account,
                    "debit": 0,
                    "credit": fee
                }
            ]
        )

    # =========================================================
    # RULE: ESCROW DEPOSIT
    # =========================================================
    async def _rule_escrow_deposit(self, db, ctx):

        escrow = ctx["escrow_account"]
        cash = ctx["cash_account"]
        amount = Decimal(str(ctx["amount"]))

        return await self.post_double_entry(
            db=db,
            reference=ctx["reference"],
            description="Escrow deposit",
            entries=[
                {
                    "account_id": escrow,
                    "debit": amount,
                    "credit": 0
                },
                {
                    "account_id": cash,
                    "debit": 0,
                    "credit": amount
                }
            ]
        )

    # =========================================================
    # RULE: REFUND
    # =========================================================
    async def _rule_refund(self, db, ctx):

        escrow = ctx["escrow_account"]
        cash = ctx["cash_account"]
        amount = Decimal(str(ctx["amount"]))

        return await self.post_double_entry(
            db=db,
            reference=ctx["reference"],
            description="Refund processed",
            entries=[
                {
                    "account_id": escrow,
                    "debit": 0,
                    "credit": amount
                },
                {
                    "account_id": cash,
                    "debit": amount,
                    "credit": 0
                }
            ]
        )

    # =========================================================
    # VALIDATION
    # =========================================================
    def _validate_entries(self, entries):
        if not entries:
            raise HTTPException(400, "No ledger entries provided")

        for e in entries:
            if "account_id" not in e:
                raise HTTPException(400, "Missing account_id")

            if Decimal(str(e.get("debit", 0))) < 0 or Decimal(str(e.get("credit", 0))) < 0:
                raise HTTPException(400, "Invalid negative entry")