from pydantic import BaseModel
from datetime import datetime


class UserResponseSchema(BaseModel):

    id: str
    full_name: str
    email: str | None = None
    phone: str | None = None

    is_active: bool
    is_verified: bool

    created_at: datetime

    # =========================================
    # SHOPPER DEFAULT LAYER
    # =========================================
    role: str = "shopper"