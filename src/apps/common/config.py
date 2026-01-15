import urllib.parse
from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings): 
    # model_config = SettingsConfigDict(
    #     env_file=".env",
    #     env_file_encoding="utf-8",
    # )

    POSTGRES_SERVER: str = '127.0.0.1'
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = 'postgres'
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "sqlbot"

    DEFAULT_PWD: str = "admin*963."

    PG_POOL_SIZE: int = 20
    PG_MAX_OVERFLOW: int = 30
    PG_POOL_RECYCLE: int = 3600
    PG_POOL_PRE_PING: bool = True

    CONTEXT_PATH: str = ""
    API_V1_STR: str = CONTEXT_PATH + "/api/v1"

    @property
    def SQLALCHEMY_DATABASE_URI(self):

        return f"postgresql+psycopg://{urllib.parse.quote(self.POSTGRES_USER)}:{urllib.parse.quote(self.POSTGRES_PASSWORD)}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()  # type: ignore
