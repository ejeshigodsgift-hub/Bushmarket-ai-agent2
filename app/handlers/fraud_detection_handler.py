class FraudDetectionHandler:

HIGH_RISK_AMOUNT = 1000000

async def handle(self, db, event):

    amount = event.get("amount", 0)

    if amount >= self.HIGH_RISK_AMOUNT:

        print(
            "[FRAUD ALERT]",
            event
        )