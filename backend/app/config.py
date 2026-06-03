from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+asyncpg://cdlaid_user:changeme@localhost:5432/cdlaid_analytics"
    )

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + self.database_url[len("postgresql://"):]
        return self.database_url

    model_config = {"env_file": ".env"}


settings = Settings()
