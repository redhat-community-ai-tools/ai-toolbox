"""MCP OAuth Library

A lightweight OAuth 2.1 + PKCE library specifically designed for MCP (Model Context Protocol) servers.
Built on top of authlib for security and standards compliance.
"""

from mcp_oauth.core.client import MCPOAuthClient
from mcp_oauth.core.models import OAuthConfig, OAuthToken, MCPOAuthState
from mcp_oauth.core.storage import TokenStorage
from mcp_oauth.integrations.fastapi import MCPOAuthMiddleware, oauth_callback_handler
from mcp_oauth.integrations.providers import (
    create_oauth_config_from_base_url,
    create_assisted_service_oauth_config,  # legacy
    create_config_from_settings,  # legacy
    get_oauth_provider_config,
    get_red_hat_sso_config  # legacy
)
from mcp_oauth.utils.browser import open_browser_for_auth
from mcp_oauth.utils.html import get_success_html

__version__ = "0.1.0"

__all__ = [
    # Core components
    "MCPOAuthClient",
    "OAuthConfig",
    "OAuthToken",
    "MCPOAuthState",
    "TokenStorage",

    # FastAPI integration
    "MCPOAuthMiddleware",
    "oauth_callback_handler",

    # Provider integrations
    "create_oauth_config_from_base_url",
    "create_assisted_service_oauth_config",  # legacy
    "create_config_from_settings",  # legacy
    "get_oauth_provider_config",
    "get_red_hat_sso_config",  # legacy

    # Utilities
    "open_browser_for_auth",
    "get_success_html",
]