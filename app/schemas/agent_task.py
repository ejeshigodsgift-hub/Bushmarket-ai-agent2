from pydantic import BaseModel, Field
from typing import Literal


class AssignAgentTaskPayload(BaseModel):

    agent_id: str = Field(..., min_length=1)

    task_type: Literal[
        "product_sourcing",
        "delivery_check",
        "supplier_contact"
    ]

    payload: dict = Field(default_factory=dict)

    cooperative_id: str | None = None