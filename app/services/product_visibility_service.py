class ProductVisibilityService:

    # =========================================
    # APPLY SHOPPER VISIBILITY RULE
    # =========================================
    def apply_visibility(self, product):

        # Only approved images are visible to shoppers
        if product.image_status != "approved":
            product.image_url = None

        return product


product_visibility_service = ProductVisibilityService()