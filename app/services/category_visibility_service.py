class CategoryVisibilityService:

    def apply_visibility(self, category):

        # Only approved category images are visible
        if category.image_status != "approved":
            category.image_url = None

        return category


category_visibility_service = CategoryVisibilityService()