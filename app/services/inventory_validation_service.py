from fastapi import HTTPException


class InventoryValidationService:

    def validate_stock(
        self,
        inventory,
        quantity: int
    ):

        if not inventory:
            raise HTTPException(
                status_code=404,
                detail="Inventory not found"
            )

        if inventory.status == "disabled":
            raise HTTPException(
                status_code=400,
                detail="Inventory disabled"
            )

        if inventory.available_stock < quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock"
            )

        return True