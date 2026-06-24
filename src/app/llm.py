from __future__ import annotations

from typing import Any

from app.config import Settings


class LlmConfigurationError(RuntimeError):
    """Raised when the optional Bedrock reasoning layer is not configured."""


def create_chat_model(settings: Settings) -> Any:
    if not settings.bedrock_model_id:
        raise LlmConfigurationError(
            "BEDROCK_MODEL_ID is not configured. Set it in .env or use --mock."
        )
    try:
        from langchain_aws import ChatBedrockConverse
    except ImportError as error:
        raise LlmConfigurationError(
            "Bedrock support is not installed. Run: uv sync --extra bedrock"
        ) from error

    arguments: dict[str, Any] = {
        "model": settings.bedrock_model_id,
        "region_name": settings.aws_region,
        "temperature": 0,
    }
    if settings.aws_profile:
        arguments["credentials_profile_name"] = settings.aws_profile
    return ChatBedrockConverse(**arguments)
