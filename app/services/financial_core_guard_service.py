class FinancialCoreGuardService:

    async def ensure_idempotency(self, db, key: str):

        result = await db.execute(
            select(FinancialTransaction)
            .where(FinancialTransaction.idempotency_key == key)
        )

        if result.scalar_one_or_none():
            return True

        return False