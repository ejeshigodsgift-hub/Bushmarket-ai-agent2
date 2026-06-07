from openai import OpenAI
import json


class LLMService:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def parse_intent(self, message: str):

        prompt = f"""
You are Bushmarket AI Router.

Classify user message into one intent only:

INTENTS:
- search_product
- add_to_cart
- price_check
- cooperative_create
- agent_request
- checkout
- general_chat

Return ONLY JSON:
{{
  "intent": "",
  "query": "",
  "quantity": null
}}

User message:
{message}
"""

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.choices[0].message.content)


llm_service = LLMService(api_key="YOUR_API_KEY")