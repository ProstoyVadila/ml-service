from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from ml_service.utils.workers import get_workers


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        frozen=True,
        extra="ignore",
    )


class PostgresConfig(Settings):
    """Configuration settings for PostgreSQL database connection."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")

    user: str = Field(alias="DB_USER", default="postgres")
    password: SecretStr = Field(alias="PASSWORD", default=SecretStr(""))
    dbname: str = Field(alias="DB", default="postgres")
    host: str = Field(alias="HOST", default="localhost")
    port: int = Field(alias="PORT", default=5432)

    pool_size: int = Field(alias="POOL_SIZE", default=16)

    @property
    def url(self) -> str:
        """Constructs the PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}"
            f"@{self.host}:{self.port}/{self.dbname}"
        )

    def __str__(self) -> str:
        """Returns the connection URL as a string."""
        return self.url


class ThrottlingConfig(Settings):
    """Configuration for throttling middleware."""

    model_config = SettingsConfigDict(env_prefix="THROTTLING_")

    rate_limit_per_minute: int = Field(alias="RATE_LIMIT_PER_MINUTE", default=60)


class BaseConfig(Settings):
    """Base configuration settings."""

    # General settings
    app_name: str = Field(alias="APP_NAME", default="autocare-ml-service")
    app_version: str = Field(alias="APP_VERSION", default="0.0.1")
    host: str = Field(alias="APP_HOST", default="0.0.0.0")
    port: int = Field(alias="APP_PORT", default=8000)
    workers: int = Field(alias="APP_WORKERS", default=get_workers())
    log_level: str = Field(alias="LOG_LEVEL", default="DEBUG")
    log_file: str = Field(alias="LOG_FILE", default="")
    is_prod: bool = Field(alias="IS_PROD", default=False)
    database: PostgresConfig = PostgresConfig()
    throttling: ThrottlingConfig = ThrottlingConfig()

    @property
    def reload(self) -> bool:
        """Determines if the application should reload based on the environment."""
        return not self.is_prod


config = BaseConfig()
