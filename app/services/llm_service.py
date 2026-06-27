from openai import OpenAI
import json


class LLMService:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def parse_intent(self, message: str, context: list = None):

        prompt = f"""
You are Bushmarket AI Router.

You understand shopping, cooperative buying, and agent workflows.

CONTEXT:
{context}

USER MESSAGE:
{message}

INTENTS:
- search_product
- select_market
- select_quantity
- confirm_checkout
- add_to_cart
- price_check
- cooperative_status
- cooperative_reminder
- cooperative_message
- cooperative_create
- agent_request
- checkout
- general_chat

RULES:
- Always extract product name into "query"
- quantity default is 1 if not stated
- If unclear, return general_chat

RETURN ONLY VALID JSON:
{{
  "intent": "",
  "query": "",
  "quantity": 1
}}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a strict JSON router."},
                {"role": "user", "content": prompt}
            ]
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {
                "intent": "general_chat",
                "query": "",
                "quantity": 1
            }


llm_service = LLMService(api_key="YOUR_API_KEY")