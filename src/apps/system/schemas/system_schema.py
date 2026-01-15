from pydantic import BaseModel, Field
from typing import Optional

class BaseUser(BaseModel):
    account: str = Field(min_length=1, max_length=100, description="用户账号")
    oid: int

class UserCreator(BaseUser):
    name: str = Field(min_length=1, max_length=100, description=f"user_name")
    email: str = Field(min_length=1, max_length=100, description=f"user_email")
    status: int = Field(default=1, description=f"status")
    origin: Optional[int] = Field(default=0, description=f"origin")
    oid_list: Optional[list[int]] = Field(default=None, description=f"oid_list")
