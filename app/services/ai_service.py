from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.pricing_service import pricing_service
from app.services.cart_service import cart_service

from app.services.ai_memory_service import ai_memory_service
from app.services.ai_logger import ai_logger

from app.services.cooperative_ai_service import (
    cooperative_ai_service
)

from app.services.cooperative_message_service import (
    cooperative_message_service
)


class AIService:

    async def process_message(
        self,
        db,
        user_id,
        message
    ):

        # =====================================
        # LOG MESSAGE
        # =====================================
        conversation_id = await ai_logger.log_user_message(
            db=db,
            user_id=user_id,
            message=message
        )

        # =====================================
        # MEMORY
        # =====================================
        memory_context = await ai_memory_service.get_relevant_memory(
            db=db,
            user_id=user_id,
            query=message
        )

        # =====================================
        # INTENT DETECTION
        # =====================================
        ai = llm_service.parse_intent(
            message=message,
            context=memory_context
        )

        intent = ai.get("intent")

        query = ai.get("query")

        quantity = ai.get("quantity") or 1

        cooperative_id = ai.get("cooperative_id")

        broadcast_message = ai.get("message")

        # =====================================
        # SEARCH
        # =====================================
        if intent == "search_product":

            results = await search_service.search_products(
                db=db,
                query=query
            )

            return {
                "reply": "Products found.",
                "results": results
            }

        # =====================================
        # PRICE CHECK
        # =====================================
        if intent == "price_check":

            listings = await search_service.search_products(
                db=db,
                query=query
            )

            if not listings:
                return {
                    "reply": "No product found."
                }

            listing = listings[0]

            breakdown = pricing_service.calculate_price(
                listing=listing,
                quantity=quantity
            )

            return {
                "reply": "Price breakdown generated.",
                "pricing": pricing_service.build_ai_response(
                    breakdown
                )
            }

        # =====================================
        # ADD TO CART
        # =====================================
        if intent == "add_to_cart":

            return await cart_service.add_item(
                db=db,
                user_id=user_id,
                listing_id=query,
                quantity=quantity
            )

        # =====================================
        # COOPERATIVE STATUS
        # =====================================
        if intent == "cooperative_status":

            return await cooperative_ai_service.get_status(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        # =====================================
        # COOPERATIVE REMINDER
        # =====================================
        if intent == "cooperative_reminder":

            return await cooperative_ai_service.send_reminder(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        # =====================================
        # COOPERATIVE MESSAGE
        # Example:
        # "Send good morning to all rice
        # cooperative members"
        # =====================================
        if intent == "cooperative_message":

            return await cooperative_message_service.broadcast(
                db=db,
                sender_id=user_id,
                cooperative_id=cooperative_id,
                message=broadcast_message
            )

        # =====================================
        # GENERAL
        # =====================================
        return {
            "reply": (
                "I can help with shopping, "
                "cooperatives and products."
            )
        }


ai_service = AIService()