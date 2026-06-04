from decimal import Decimal

from app.db.models.commission_distribution import (
    CommissionDistribution
)


class CommissionDistributionService:

    async def build_distribution(
        self,
        db,
        order,
        order_item
    ):

        gross_amount = Decimal(
            str(order_item.total_price)
        )

        platform_amount = Decimal(
            str(order_item.platform_fee_amount)
        )

        market_amount = Decimal(
            str(order_item.market_fee_amount)
        )

        agent_amount = Decimal(
            str(order_item.agent_fee_amount)
        )

        seller_amount = (
            gross_amount
            - platform_amount
            - market_amount
            - agent_amount
        )

        distribution = CommissionDistribution(
            order_id=order.id,
            order_item_id=order_item.id,
            gross_amount=gross_amount,
            seller_amount=seller_amount,
            platform_amount=platform_amount,
            market_amount=market_amount,
            agent_amount=agent_amount,
            status="pending"
        )

        db.add(distribution)

        return distribution