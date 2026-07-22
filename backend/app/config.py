from pathlib import Path
from pydantic_settings import BaseSettings


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    database_url: str

    @property
    def async_database_url(self):
        if self.database_url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + self.database_url[len("postgresql://"):]
        return self.database_url

    model_config = {
        "env_file": BASE_DIR / ".env",
        "extra": "ignore",
    }


settings = Settings()

# from pydantic_settings import BaseSettings



# class Settings(BaseSettings):
#     db_host: str = "localhost"
#     db_port: int = 5432
#     db_name: str = "cdlaid_analytics"
#     db_user: str = "cdlaid_user"
#     db_password: str

#     @property
#     def database_url(self):
#         return (
#             f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
#             f"@{self.db_host}:{self.db_port}/{self.db_name}"
#         )

#     model_config = {
#         "env_file": ".env",
#         "extra": "ignore"
#     }


# settings = Settings()
