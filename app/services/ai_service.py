from app.services.llm_service import llm_service
from app.services.search_service import search_service
from app.services.pricing_service import pricing_service
from app.services.cart_service import cart_service


class AIService:

    async def process_message(self, db, user_id, message):

        # 1. OpenAI ONLY decides intent
        ai = llm_service.parse_intent(message)

        intent = ai["intent"]
        query = ai.get("query")
        quantity = ai.get("quantity") or 1

        # 2. ROUTING LAYER

        # SEARCH
        if intent == "search_product":
            results = await search_service.search_products(db, query)

            return {
                "reply": "Here are products found",
                "results": results
            }

        # PRICE CHECK
        if intent == "price_check":
            listing = await search_service.search_products(db, query)
            listing = listing[0]

            breakdown = pricing_service.calculate_price(
                listing=listing,
                quantity=quantity
            )

            return pricing_service.build_ai_response(breakdown)

        # ADD TO CART
        if intent == "add_to_cart":
            return await cart_service.add_item(
                db=db,
                user_id=user_id,
                listing_id=query,
                quantity=quantity
            )

        # GENERAL
        return {
            "reply": "I can help you shop, search, or buy products."
        }


ai_service = AIService()