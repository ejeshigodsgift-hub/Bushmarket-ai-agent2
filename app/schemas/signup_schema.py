from pydantic import BaseModel, Field, model_validator


class SignupSchema(BaseModel):

    full_name: str = Field(..., min_length=2)

    email: str | None = Field(
        default=None,
        description="Optional email (rural-first design)"
    )

    phone: str | None = Field(
        default=None,
        description="Optional phone number (rural-first design)"
    )

    password: str = Field(..., min_length=6)

    # =========================================
    # VALIDATION RULE: email OR phone required
    # =========================================
    @model_validator(mode="after")
    def validate_contact(cls, values):

        if not values.email and not values.phone:
            raise ValueError("Either email or phone is required")

        return values