from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.pricing_service import pricing_service
from app.services.cart_service import cart_service

# 🆕 NEW (you will create these)
from app.services.ai_memory_service import ai_memory_service
from app.services.ai_logger import ai_logger


class AIService:

    async def process_message(self, db, user_id, message):

        # =====================================================
        # 1. LOG USER INPUT (DATA LAYER)
        # =====================================================
        await ai_logger.log_user_message(
            db=db,
            user_id=user_id,
            message=message
        )

        # =====================================================
        # 2. RETRIEVE MEMORY (RAG STEP)
        # =====================================================
        memory_context = await ai_memory_service.get_relevant_memory(
            db=db,
            user_id=user_id,
            query=message
        )

        # =====================================================
        # 3. OPENAI INTENT PARSING (WITH MEMORY CONTEXT)
        # =====================================================
        ai = llm_service.parse_intent(
            message=message,
            context=memory_context
        )

        intent = ai["intent"]
        query = ai.get("query")
        quantity = ai.get("quantity") or 1

        # =====================================================
        # 4. ROUTING LAYER
        # =====================================================

        # -------------------------
        # SEARCH
        # -------------------------
        if intent == "search_product":
            results = await search_service.search_products(db, query)

            await ai_logger.log_system_action(
                db=db,
                user_id=user_id,
                action="search_product",
                data={"query": query}
            )

            return {
                "reply": "Here are products found",
                "results": results
            }

        # -------------------------
        # PRICE CHECK
        # -------------------------
        if intent == "price_check":

            listings = await search_service.search_products(db, query)

            if not listings:
                return {"reply": "No product found"}

            listing = listings[0]

            breakdown = pricing_service.calculate_price(
                listing=listing,
                quantity=quantity
            )

            await ai_logger.log_system_action(
                db=db,
                user_id=user_id,
                action="price_check",
                data={
                    "listing_id": listing.id,
                    "quantity": quantity
                }
            )

            return pricing_service.build_ai_response(breakdown)

        # -------------------------
        # ADD TO CART
        # -------------------------
        if intent == "add_to_cart":

            result = await cart_service.add_item(
                db=db,
                user_id=user_id,
                listing_id=query,
                quantity=quantity
            )

            await ai_logger.log_system_action(
                db=db,
                user_id=user_id,
                action="add_to_cart",
                data={
                    "listing_id": query,
                    "quantity": quantity
                }
            )

            return result

        # -------------------------
        # GENERAL
        # -------------------------
        return {
            "reply": "I can help you shop, search, or buy products."
        }


ai_service = AIService()