from datetime import datetime, timedelta
from typing import List
import hashlib
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.cooperative import Cooperative
from app.db.models.cooperative_procurement import CooperativeProcurement
from app.db.models.cooperative_merge_proposal import CooperativeMergeProposal
from app.db.models.cooperative_merge_proposal_cooperative import (
    CooperativeMergeProposalCooperative
)

from app.services.outbox_service import outbox_service
from app.services.cooperative_state_service import cooperative_state_service


class CooperativeMergeService:
    """
    Detects merge candidates + generates merge proposals + executes merge
    """

    # =====================================================
    # HASH BUILDER (CORE FIX)
    # =====================================================
    def build_target_product_hash(self, product_ids: list) -> str:
        """
        Creates deterministic hash for product comparison
        """
        normalized = sorted(product_ids or [])
        return hashlib.sha256(
            json.dumps(normalized).encode()
        ).hexdigest()

    # =====================================================
    # FIND CANDIDATES
    # =====================================================
    async def find_merge_candidates(self, db: AsyncSession) -> List[Cooperative]:

        stmt = select(Cooperative).where(
            Cooperative.status == "active",
            Cooperative.ends_at > datetime.utcnow()
        )

        result = await db.execute(stmt)
        return result.scalars().all()

    # =====================================================
    # BUILD GROUPS (FIXED LOGIC)
    # =====================================================
    async def build_merge_groups(
        self,
        cooperatives: List[Cooperative]
    ) -> List[List[Cooperative]]:

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

                # =========================================
                # ✅ CORE RULE: SAME TARGET PRODUCT HASH
                # =========================================
                if (
                    other.target_product_hash
                    == coop.target_product_hash
                ):
                    group.append(other)
                    used.add(other.id)

            if len(group) > 1:
                groups.append(group)

        return groups

    # =====================================================
    # GENERATE MERGE PROPOSALS
    # =====================================================
    async def generate_merge_proposals(self, db: AsyncSession):

        cooperatives = await self.find_merge_candidates(db)
        groups = await self.build_merge_groups(cooperatives)

        proposals = []

        for group in groups:

            proposal = CooperativeMergeProposal(
                approval_threshold=70,
                expires_at=datetime.utcnow() + timedelta(hours=48),
                status="voting"
            )

            db.add(proposal)
            await db.flush()

            # link cooperatives
            for coop in group:
                db.add(
                    CooperativeMergeProposalCooperative(
                        proposal_id=proposal.id,
                        cooperative_id=coop.id
                    )
                )

            proposals.append(proposal.id)

            await outbox_service.queue_event(
                db,
                "cooperative.merge.proposal.created",
                {
                    "proposal_id": proposal.id,
                    "cooperative_ids": [c.id for c in group],
                    "status": "voting"
                }
            )

        await db.commit()
        return proposals

    # =====================================================
    # EXECUTE MERGE
    # =====================================================
    async def execute_merge(
        self,
        db: AsyncSession,
        cooperatives: List[Cooperative],
    ):

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

        merged = await merger.merge_procurements(
            db=db,
            cooperative_id=cooperatives[0].id,
            procurements=all_procurements
        )

        for coop in cooperatives:
            await cooperative_state_service.transition(
                db=db,
                cooperative=coop,
                new_state="procurement_pending",
                reason="cooperative_merge_executed"
            )

        await outbox_service.queue_event(
            db,
            "cooperative.merge.executed",
            {
                "merged_id": merged.id,
                "cooperatives": [c.id for c in cooperatives]
            }
        )

        await db.commit()
        return merged


cooperative_merge_service = CooperativeMergeService()