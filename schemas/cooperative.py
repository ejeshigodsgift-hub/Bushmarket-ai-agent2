from pydantic import BaseModel


class CooperativeCreate(BaseModel):
    product_id: str
    category: str | None = None
    quantity_target: int
    member_target: int
    contribution_amount: float