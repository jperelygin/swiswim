from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # general
    env: str = ""
    debug: bool = False

    # database
    db_host: str = ""
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    # security
    bcrypt_rounds: int = 12

    # auth
    jwt_secret_key: str = ""
    jwt_algorithm: str = ""
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7

    # rate limiter
    auth_rate_limit: str = "5 per 15 minutes"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()