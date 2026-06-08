from uuid import uuid4

from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.pricing_service import pricing_service
from app.services.cart_service import cart_service

from app.services.ai_memory_service import ai_memory_service
from app.services.ai_logger import ai_logger

from app.services.cooperative_ai_service import cooperative_ai_service
from app.services.cooperative_message_service import cooperative_message_service

from app.db.models.ai_product_recommendation import AIProductRecommendation
from app.services.stt_service import stt_service


class AIService:

    async def process_message(
        self,
        db,
        user_id: str,
        message: str | None = None,
        audio_file=None
    ):
        # =====================================================
        # SESSION
        # =====================================================
        session_id = str(uuid4())

        conversation = await ai_logger.get_or_create_conversation(
            db=db,
            user_id=user_id
        )
        conversation_id = conversation.id

        # =====================================================
        # VOICE INPUT
        # =====================================================
        if audio_file:
            message = await stt_service.transcribe(audio_file)

        if not message:
            raise ValueError("No input provided")

        # =====================================================
        # LOG USER MESSAGE
        # =====================================================
        await ai_logger.log_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=message,
            metadata={"session_id": session_id}
        )

        # =====================================================
        # MEMORY
        # =====================================================
        memory_context = await ai_memory_service.get_relevant_memory(
            db=db,
            user_id=user_id,
            query=message
        )

        # =====================================================
        # INTENT PARSING
        # =====================================================
        ai = llm_service.parse_intent(
            message=message,
            context=memory_context
        )

        intent = ai.get("intent")
        query = ai.get("query") or message
        quantity = ai.get("quantity") or 1
        cooperative_id = ai.get("cooperative_id")
        broadcast_message = ai.get("message")

        data = {}
        reply = "Processing request..."
        recommendations = []

        # =====================================================
        # SEARCH PRODUCTS
        # =====================================================
        if intent == "search_product":

            listings = await search_service.search_products(
                db=db,
                query=query
            )

            recommendations = listings

            data = {
    "results": search_service.to_api_response(listings)
            }

            reply = "Products found."

        # =====================================================
        # PRICE CHECK
        # =====================================================
        elif intent == "price_check":

            listings = await search_service.search_products(
                db=db,
                query=query
            )

            if not listings:
                reply = "No product found."
                data = {}

            else:
                listing = listings[0]
                recommendations = [listing]

                breakdown = pricing_service.calculate_price(
                    listing=listing,
                    quantity=quantity
                )

                data = pricing_service.build_ai_response(breakdown)
                reply = "Price breakdown ready."

        # =====================================================
        # ADD TO CART
        # =====================================================
        elif intent == "add_to_cart":

            result = await cart_service.add_item(
                db=db,
                user_id=user_id,
                listing_id=query,
                quantity=quantity
            )

            await ai_logger.log_behavior_signal(
                db=db,
                user_id=user_id,
                    conversation_id=conversation_id,
                event="add_to_cart",
                listing_id=query,
                session_id=session_id
            )

            data = result
            reply = "Added to cart."

        # =====================================================
        # COOPERATIVE STATUS
        # =====================================================
        elif intent == "cooperative_status":

            data = await cooperative_ai_service.get_status(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )
            reply = "Cooperative status retrieved."

        # =====================================================
        # COOPERATIVE REMINDER
        # =====================================================
        elif intent == "cooperative_reminder":

            data = await cooperative_ai_service.send_reminder(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )
            reply = "Reminder sent."

        # =====================================================
        # COOPERATIVE MESSAGE
        # =====================================================
        elif intent == "cooperative_message":

            data = await cooperative_message_service.broadcast(
                db=db,
                sender_id=user_id,
                cooperative_id=cooperative_id,
                message=broadcast_message
            )
            reply = "Message sent to cooperative."

        # =====================================================
        # DEFAULT RESPONSE
        # =====================================================
        else:
            data = {}
            reply = "I can help you shop, search, or manage cooperatives."

        # =====================================================
        # LOG AI RECOMMENDATIONS (LEARNING LAYER)
        # =====================================================
        for rank, listing in enumerate(recommendations[:5], start=1):

            listing_id = getattr(listing, "listing_id", None) or getattr(listing, "id", None)

            db.add(
                AIProductRecommendation(
                    conversation_id=conversation_id,
                    listing_id=listing_id,
                    confidence_score=ai.get("confidence", 0.8),
                    rank_position=rank,
                    reasoning=ai.get("reasoning"),
                    model_version="v1",
                    clicked=False,
                    added_to_cart=False,
                    purchased=False
                )
            )

        # =====================================================
        # LOG ASSISTANT MESSAGE
        # =====================================================
        await ai_logger.log_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=reply,
            metadata={
                "session_id": session_id,
                "intent": intent
            }
        )

        # =====================================================
        # COMMIT
        # =====================================================
        await db.commit()

        # =====================================================
        # FINAL RESPONSE
        # =====================================================
        return {
            "reply": reply,
            "data": data,
            "intent": intent,
            "session_id": session_id
        }


ai_service = AIService()