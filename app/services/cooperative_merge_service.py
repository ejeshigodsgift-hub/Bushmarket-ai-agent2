from datetime import datetime, timedelta
from typing import List, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_procurement import CooperativeProcurement
from app.services.outbox_service import outbox_service


class CooperativeMergeService:
    """
    Detects merge candidates + generates merge proposals + triggers workflow
    """

    # =========================================================
    # 1. CANDIDATE DISCOVERY ENGINE
    # =========================================================
    async def find_merge_candidates(self, db: AsyncSession) -> List[Cooperative]:
        """
        Find cooperatives eligible for merge based on:
        - same product intent (simplified placeholder: same status + funding)
        - similar lifecycle stage
        - not expired
        """

        stmt = select(Cooperative).where(
            Cooperative.status.in_(["active", "funding"]),
            Cooperative.ends_at > datetime.utcnow()
        )

        result = await db.execute(stmt)
        cooperatives = result.scalars().all()

        # Grouping logic placeholder (can be upgraded to AI clustering later)
        return cooperatives

    # =========================================================
    # 2. MERGE GROUP BUILDER
    # =========================================================
    async def build_merge_groups(self, cooperatives: List[Cooperative]) -> List[List[Cooperative]]:
        """
        Simple deterministic grouping engine.
        Later upgrade: AI-based product similarity clustering.
        """

        groups = []
        used = set()

        for coop in cooperatives:
            if coop.id in used:
                continue

            group = [coop]
            used.add(coop.id)

            for other in cooperatives:
                if other.id in used:
                    continue

                # SIMPLE RULE: same market + similar end time window
                if (
                    other.market_id == coop.market_id and
                    abs((other.ends_at - coop.ends_at).total_seconds()) < 3600 * 24
                ):
                    group.append(other)
                    used.add(other.id)

            if len(group) > 1:
                groups.append(group)

        return groups

    # =========================================================
    # 3. MERGE PROPOSAL GENERATION
    # =========================================================
    async def generate_merge_proposals(self, db: AsyncSession):

        cooperatives = await self.find_merge_candidates(db)
        groups = await self.build_merge_groups(cooperatives)

        proposals = []

        for group in groups:

            proposal = {
                "id": f"merge_{datetime.utcnow().timestamp()}",
                "cooperative_ids": [c.id for c in group],
                "status": "voting",
                "created_at": datetime.utcnow(),
                "approval_threshold": 100
            }

            proposals.append(proposal)

            await outbox_service.queue_event(
                db,
                "cooperative.merge.proposal.created",
                proposal
            )

        await db.commit()
        return proposals

    # =========================================================
    # 4. EXECUTE MERGE
    # =========================================================
    async def execute_merge(
        self,
        db: AsyncSession,
        cooperatives: List[Cooperative],
    ):
        """
        Converts multiple cooperatives → single merged procurement context
        """

        from app.services.cooperative_merge_procurement_service import (
            CooperativeMergeProcurementService
        )

        all_procurements = []

        for coop in cooperatives:

            stmt = select(CooperativeProcurement).where(
                CooperativeProcurement.cooperative_id == coop.id,
                CooperativeProcurement.status.in_(["approved", "pending"])
            )

            result = await db.execute(stmt)
            all_procurements.extend(result.scalars().all())

        if not all_procurements:
            raise ValueError("No procurements available for merge")

        merger = CooperativeMergeProcurementService()

        merged = merger.merge_procurements(
            db=db,
            cooperative_id=cooperatives[0].id,
            procurements=all_procurements
        )

        for coop in cooperatives:
            coop.status = "merged"

        await db.commit()

        await outbox_service.queue_event(
            db,
            "cooperative.merge.executed",
            {
                "merged_id": merged.id,
                "cooperatives": [c.id for c in cooperatives]
            }
        )

        return merged


cooperative_merge_service = CooperativeMergeService()