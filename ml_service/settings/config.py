from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        frozen=True,
        extra="ignore",
    )


class PostgresConfig(Settings):
    user: str = Field(alias="DB_USER", default="postgres")
    password: SecretStr = Field(alias="PASSWORD", default=SecretStr(""))
    dbname: str = Field(alias="DB", default="postgres")
    host: str = Field(alias="HOST", default="localhost")
    port: int = Field(alias="PORT", default=5432)

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class BaseConfig(Settings):
    """Base configuration settings."""

    # General settings
    app_name: str = Field(alias="APP_NAME", default="autocare-ml-service")
    app_version: str = Field(alias="APP_VERSION", default="0.0.1")
    log_level: str = Field(alias="LOG_LEVEL", default="DEBUG")
    log_file: str = Field(alias="LOG_FILE", default="")
    is_prod: bool = Field(alias="IS_PROD", default=False)
    database: PostgresConfig = PostgresConfig()


config = BaseConfig()
