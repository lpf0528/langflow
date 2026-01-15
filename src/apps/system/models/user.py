
from src.apps.common.models import SnowflakeBase
from sqlmodel import Field, SQLModel, BigInteger
from src.apps.common.security import default_md5_pwd
from src.apps.common.utils import get_timestamp

class BaseUserPO(SQLModel):
    account: str = Field(max_length=255, unique=True)
    oid: int = Field(nullable=False, sa_type=BigInteger(), default=0)
    name: str = Field(max_length=255, unique=True)
    age: int = Field(default=0, nullable=False)
    password: str = Field(default_factory=default_md5_pwd, max_length=255)
    email: str = Field(max_length=255)
    status: int = Field(default=0, nullable=False)
    origin: int = Field(nullable=False, default=0)
    create_time: int = Field(default_factory=get_timestamp, sa_type=BigInteger(), nullable=False)
    language: str = Field(max_length=255, default="zh-CN")

class UserModel(SnowflakeBase, BaseUserPO, table=True):
    __tablename__ = "user"