from utils.ai_prompt_builder import build_ai_prompt


class AINotificationEngine:

    def generate_message(self, event_type: str, payload: dict):

        prompt = build_ai_prompt(event_type, payload)

        # Simulated AI response (replace with OpenAI / LLM later)
        if event_type == "funding_50_percent":
            return "🔥 Great progress! Your cooperative is 50% funded. Invite more members to complete faster."

        if event_type == "cooperative_funded":
            return "🎉 Cooperative fully funded! Preparing bulk purchase now."

        if event_type == "delivery_completed":
            return "📦 Delivery completed successfully. All members can now confirm receipt."

        if event_type == "payment_failed":
            return "⚠️ Payment failed. Please retry to secure your spot in the cooperative."

        return "📢 Update from Bushmarket Cooperative."