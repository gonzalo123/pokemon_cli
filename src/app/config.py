from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    aws_profile: str | None = Field(default=None, validation_alias="AWS_PROFILE")
    aws_region: str = Field(default="eu-west-1", validation_alias="AWS_REGION")
    bedrock_model_id: str | None = Field(default=None, validation_alias="BEDROCK_MODEL_ID")
    pokeapi_timeout: float = Field(default=10.0, validation_alias="POKEAPI_TIMEOUT")
