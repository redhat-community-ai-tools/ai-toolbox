"""Framework integrations for MCP OAuth."""

from .fastapi import MCPOAuthMiddleware, create_oauth_middleware, oauth_callback_handler
from .providers import (
    create_oauth_config_from_base_url,
    create_assisted_service_oauth_config,  # legacy
    create_config_from_settings,  # legacy
    get_oauth_provider_config,
    get_red_hat_sso_config,  # legacy
    OAUTH_PROVIDER_CONFIGS
)

__all__ = [
    # FastAPI integration
    "MCPOAuthMiddleware",
    "create_oauth_middleware",
    "oauth_callback_handler",

    # Provider integrations
    "create_oauth_config_from_base_url",
    "create_assisted_service_oauth_config",  # legacy
    "create_config_from_settings",  # legacy
    "get_oauth_provider_config",
    "get_red_hat_sso_config",  # legacy
    "OAUTH_PROVIDER_CONFIGS",
]