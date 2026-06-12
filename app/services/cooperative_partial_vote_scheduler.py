class CooperativePartialVoteScheduler:

    async def close_expired_votes(
        self,
        db
    ):
        now = datetime.now(timezone.utc)

        stmt = select(
            CooperativePartialProcurementProposal
        ).where(
            CooperativePartialProcurementProposal.status
            == "voting",
            CooperativePartialProcurementProposal.expires_at
            <= now
        )

        proposals = (
            await db.execute(stmt)
        ).scalars().all()

        for proposal in proposals:
            await (
                CooperativePartialVotingService()
                .evaluate_votes(
                    db,
                    proposal
                )
            )