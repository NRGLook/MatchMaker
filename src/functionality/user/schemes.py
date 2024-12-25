from typing import Optional

from pydantic import BaseModel, Field, PositiveInt


class UserSchema(BaseModel):
    first_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Name of user"
    )
    last_name: Optional[str] = Field(
        None,
        max_length=255,
        description="Last name of user"
    )
    age: Optional[PositiveInt] = Field(
        None,
        description="Age of user (should be grater than 0)"
    )
    experience: Optional[PositiveInt] = Field(
        None,
        description="Experience of user (age)"
    )
