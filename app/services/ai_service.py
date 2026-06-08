from datetime import datetime
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

# =====================================================
# 🧠 VOICE INTEGRATION (NEW LAYER)
# =====================================================
from app.services.stt_service import stt_service  # Speech-to-text service


class AIService:

    # =====================================================
    # MAIN ENTRY (NOW SUPPORTS TEXT OR AUDIO)
    # =====================================================
    async def process_message(
        self,
        db,
        user_id: str,
        message: str | None = None,
        audio_file=None
    ):

        # =====================================================
        # 0. SESSION CONTEXT
        # =====================================================
        session_id = str(uuid4())

        conversation = await ai_logger.get_or_create_conversation(
            db=db,
            user_id=user_id
        )
        conversation_id = conversation.id

        # =====================================================
        # 🧠 VOICE INGESTION LAYER (NEW)
        # =====================================================
        if audio_file is not None:
            message = await stt_service.transcribe(audio_file)

        # fallback safety
        if not message:
            raise ValueError("No input provided (text or audio required)")

        # =====================================================
        # 1. LOG USER MESSAGE (UNIFIED PIPELINE)
        # =====================================================
        await ai_logger.log_message(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=message,
            metadata={
                "session_id": session_id,
                "source": "voice" if audio_file else "chat"
            }
        )

        # =====================================================
        # 2. MEMORY CONTEXT (RAG)
        # =====================================================
        memory_context = await ai_memory_service.get_relevant_memory(
            db=db,
            user_id=user_id,
            query=message
        )

        # =====================================================
        # 3. INTENT PARSING
        # =====================================================
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
        recommendations = []

        # =====================================================
        # SEARCH PRODUCT
        # =====================================================
        if intent == "search_product":

            listings = await search_service.search_products(
                db=db,
                query=query
            )

            recommendations = listings

            response_payload = {
                "reply": "Products found.",
                "results": listings
            }

        # =====================================================
        # PRICE CHECK
        # =====================================================
        elif intent == "price_check":

            listings = await search_service.search_products(
                db=db,
                query=query
            )

            if not listings:
                response_payload = {
                    "reply": "No product found."
                }

            else:
                listing = listings[0]

                recommendations = [listing]

                breakdown = pricing_service.calculate_price(
                    listing=listing,
                    quantity=quantity
                )

                response_payload = {
                    "reply": "Price breakdown generated.",
                    "pricing": pricing_service.build_ai_response(breakdown)
                }

        # =====================================================
        # ADD TO CART (FEEDBACK LOOP)
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
                event="add_to_cart",
                listing_id=query,
                session_id=session_id
            )

            response_payload = result

        # =====================================================
        # COOPERATIVE ACTIONS
        # =====================================================
        elif intent == "cooperative_status":

            response_payload = await cooperative_ai_service.get_status(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        elif intent == "cooperative_reminder":

            response_payload = await cooperative_ai_service.send_reminder(
                db=db,
                user_id=user_id,
                cooperative_id=cooperative_id
            )

        elif intent == "cooperative_message":

            response_payload = await cooperative_message_service.broadcast(
                db=db,
                sender_id=user_id,
                cooperative_id=cooperative_id,
                message=broadcast_message
            )

        # =====================================================
        # DEFAULT RESPONSE
        # =====================================================
        else:
            response_payload = {
                "reply": "I can help with shopping, cooperatives and products."
            }

        # =====================================================
        # 4. AI PRODUCT RECOMMENDATION LOGGING
        # =====================================================
        for rank, listing in enumerate(recommendations[:5], start=1):

            db.add(
                AIProductRecommendation(
                    conversation_id=conversation_id,
                    listing_id=getattr(listing, "id", None),
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
        # 5. LOG ASSISTANT MESSAGE
        # =====================================================
        assistant_text = (
            response_payload.get("reply")
            if isinstance(response_payload, dict)
            else str(response_payload)
        )

        await ai_logger.log_message(
            db=db,
            conversation_id=conversation_id,
            role="assistant",
            content=assistant_text,
            metadata={
                "session_id": session_id,
                "intent": intent
            }
        )

        # =====================================================
        # 6. COMMIT ALL
        # =====================================================
        await db.commit()

        # =====================================================
        # 7. RETURN RESPONSE
        # =====================================================
        return response_payload


ai_service = AIService()