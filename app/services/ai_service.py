# app/services/ai_service.py

from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.pricing_service import pricing_service
from app.services.cart_service import cart_service

from app.services.ai_memory_service import ai_memory_service
from app.services.ai_logger import ai_logger

from app.services.cooperative_ai_service import cooperative_ai_service
from app.services.cooperative_message_service import cooperative_message_service


class AIService:

    async def process_message(self, db, user_id, message):

        # =====================================
        # 1. LOG USER MESSAGE (GET CONVERSATION)
        # =====================================
        conversation_id = await ai_logger.log_user_message(
            db=db,
            user_id=user_id,
            message=message
        )

        # =====================================
        # 2. MEMORY CONTEXT
        # =====================================
        memory_context = await ai_memory_service.get_relevant_memory(
            db=db,
            user_id=user_id,
            query=message
        )

        # =====================================
        # 3. INTENT PARSING
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

        response_payload = None

        # =====================================
        # SEARCH
        # =====================================
        if intent == "search_product":

            results = await search_service.search_products(db=db, query=query)

            response_payload = {
                "reply": "Products found.",
                "results": results
            }

        # =====================================
        # PRICE CHECK
        # =====================================
        elif intent == "price_check":

            listings = await search_service.search_products(db=db, query=query)

            if not listings:
                response_payload = {"reply": "No product found."}
            else:
                listing = listings[0]

                breakdown = pricing_service.calculate_price(
                    listing=listing,
                    quantity=quantity
                )

                response_payload = {
                    "reply": "Price breakdown generated.",
                    "pricing": pricing_service.build_ai_response(breakdown)
                }

        # =====================================
        # ADD TO CART
        # =====================================
        elif intent == "add_to_cart":

            result = await cart_service.add_item(
                db=db,
                user_id=user_id,
                listing_id=query,
                quantity=quantity
            )

            response_payload = result

        # =====================================
        # COOPERATIVE STATUS
        # =====================================
        elif intent == "cooperative_status":

            response_payload = await cooperative_ai_service.get_status(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        # =====================================
        # COOPERATIVE REMINDER
        # =====================================
        elif intent == "cooperative_reminder":

            response_payload = await cooperative_ai_service.send_reminder(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        # =====================================
        # COOPERATIVE MESSAGE
        # =====================================
        elif intent == "cooperative_message":

            response_payload = await cooperative_message_service.broadcast(
                db=db,
                sender_id=user_id,
                cooperative_id=cooperative_id,
                message=broadcast_message
            )

        # =====================================
        # DEFAULT
        # =====================================
        else:
            response_payload = {
                "reply": "I can help with shopping, cooperatives and products."
            }

        # =====================================
        # 4. LOG ASSISTANT MESSAGE (FIXED)
        # =====================================
        assistant_text = response_payload.get("reply", "Done")

        await ai_logger.log_assistant_message(
            db=db,
            conversation_id=conversation_id,
            message=assistant_text
        )

        # =====================================
        # 5. RETURN RESPONSE
        # =====================================
        return response_payload


ai_service = AIService()