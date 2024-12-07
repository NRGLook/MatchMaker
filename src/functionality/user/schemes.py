from pydantic import BaseModel, Field, PositiveInt
from typing import Optional


class UserSchema(BaseModel):
    first_name: Optional[str] = Field(None, max_length=255, description="Имя пользователя")
    last_name: Optional[str] = Field(None, max_length=255, description="Фамилия пользователя")
    age: Optional[PositiveInt] = Field(None, description="Возраст пользователя (должен быть > 0)")
    experience: Optional[PositiveInt] = Field(None, description="Опыт работы пользователя в годах")
