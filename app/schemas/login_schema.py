from pydantic import BaseModel, Field


class LoginSchema(BaseModel):

    # =========================================
    # IDENTIFIER (EMAIL OR PHONE)
    # =========================================
    identifier: str = Field(
        ...,
        description="Email or phone number used to login"
    )

    # =========================================
    # PASSWORD
    # =========================================
    password: str = Field(
        ...,
        min_length=6,
        description="User account password"
    )