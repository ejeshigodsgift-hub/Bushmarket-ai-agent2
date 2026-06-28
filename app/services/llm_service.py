from openai import AsyncOpenAI
import json

from app.core.config import settings

import logging

logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    # =====================================================
    # INTENT ROUTER
    # =====================================================
    async def parse_intent(
        self,
        message: str,
        context: list | None = None
    ):

        prompt = f"""
    You are Bushmarket AI Router.

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

    RETURN ONLY VALID JSON:
    {{
      "intent": "",
      "query": "",
      "quantity": 1
    }}
    """

        try:

            response = await  self.client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type":  "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": "You are a strict JSON router."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

        except Exception:

            logger.exception("OpenAI Failure")
            raise

        try:

            return json.loads(
             response.choices[0].message.content
            )

        except Exception as e:

            logger.exception(
                f"Intent Parse Failure: {str(e)}"
            )

            return {
                "intent": "general_chat",
                "query": "",
                "quantity": 1
            }
    # =====================================================
    # CONVERSATION SUMMARIZER
    # =====================================================
    def summarize_conversation(
        self,
        existing_summary: str,
        messages: list[dict]
    ):

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You summarize conversations. "
                        "Keep important user preferences, "
                        "shopping interests, products discussed, "
                        "cooperative activities, decisions made, "
                        "agent requests, checkout actions, and "
                        "important context needed for future chats. "
                        "Return only the updated summary."
                    )
                },
                {
                    "role": "user",
                    "content": f"""
EXISTING SUMMARY:
{existing_summary}

NEW MESSAGES:
{json.dumps(messages, ensure_ascii=False)}

Create an updated conversation summary.
"""
                }
            ]
        )

        usage = response.usage

        prompt_tokens = usage.prompt_tokens
        completion_tokens =   usage.completion_tokens
        total_tokens = usage.total_tokens

        estimated_cost = (
            prompt_tokens * 0.00000015
        ) + (
            completion_tokens * 0.00000060
        )

        

        return {
            "summary": response.choices[0].message.content.strip(),
            "prompt_tokens": prompt_tokens,
            "completion_tokens":    completion_tokens,
            "total_tokens": total_tokens,
            "estimated_cost": estimated_cost
        }


llm_service = LLMService(
    api_key=settings.OPENAI_API_KEY
)