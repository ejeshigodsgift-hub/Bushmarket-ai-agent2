from decimal import Decimal
from typing import Dict, List

from fastapi import HTTPException


class LedgerPostingRulesEngine:
    """
    Maps business events → double-entry accounting instructions
    """

    def __init__(self):
        self.rules = self._load_rules()

    # =====================================================
    # RULE REGISTRY
    # =====================================================
    def _load_rules(self) -> Dict:

        return {
            # =========================================
            # WALLET TOPUP
            # User deposits money into system
            # =========================================
            "wallet_topup": {
                "debit": "escrow",
                "credit": "wallet",
                "description": "Wallet top-up"
            },

            # =========================================
            # ORDER PAYMENT
            # User pays for goods/services
            # =========================================
            "order_payment": {
                "debit": "wallet",
                "credit": "escrow",
                "description": "Order payment into escrow"
            },

            # =========================================
            # ESCROW RELEASE
            # Money released to platform/supplier
            # =========================================
            "escrow_release": {
                "debit": "escrow",
                "credit": "platform",
                "description": "Escrow release to platform"
            },

            # =========================================
            # REFUND
            # Money returned to wallet
            # =========================================
            "refund": {
                "debit": "escrow",
                "credit": "wallet",
                "description": "Refund processed"
            },

            # =========================================
            # COMMISSION EARNED
            # Platform earns fee
            # =========================================
            "commission_fee": {
                "debit": "escrow",
                "credit": "platform",
                "description": "Platform commission fee"
            }
        }

    # =====================================================
    # GET RULE
    # =====================================================
    def get_rule(self, event: str) -> Dict:
        rule = self.rules.get(event)

        if not rule:
            raise HTTPException(
                status_code=400,
                detail=f"No ledger rule defined for event: {event}"
            )

        return rule

    # =====================================================
    # BUILD LEDGER POSTING STRUCTURE
    # =====================================================
    def build_posting(
        self,
        event: str,
        amount: Decimal,
        accounts: Dict[str, str],
        reference: str,
        extra: dict | None = None
    ) -> List[Dict]:
        """
        Converts rule → ledger engine format
        """

        rule = self.get_rule(event)

        debit_account_type = rule["debit"]
        credit_account_type = rule["credit"]

        debit_account = accounts.get(debit_account_type)
        credit_account = accounts.get(credit_account_type)

        if not debit_account or not credit_account:
            raise HTTPException(
                status_code=400,
                detail=f"Missing account mapping for event {event}"
            )

        return [
            {
                "account_id": debit_account,
                "debit": amount,
                "credit": 0
            },
            {
                "account_id": credit_account,
                "debit": 0,
                "credit": amount
            }
        ]

    # =====================================================
    # ENRICHED POSTING (WITH DESCRIPTION)
    # =====================================================
    def build_enriched_posting(
        self,
        event: str,
        amount: Decimal,
        accounts: Dict[str, str],
        reference: str,
        extra: dict | None = None
    ):
        rule = self.get_rule(event)

        entries = self.build_posting(
            event=event,
            amount=amount,
            accounts=accounts,
            reference=reference,
            extra=extra
        )

        return {
            "reference": reference,
            "description": rule["description"],
            "entries": entries
        }