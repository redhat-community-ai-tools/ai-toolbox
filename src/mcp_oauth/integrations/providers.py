"""OAuth provider configurations and utilities."""

from typing import Optional
from ..core.models import OAuthConfig


def create_oauth_config_from_base_url(
    base_url: str,
    oauth_url: str,
    oauth_client: str,
    oauth_redirect_uri: Optional[str] = None,
    scope: str = "openid profile email"
) -> OAuthConfig:
    """Create OAuth configuration from base server URL and OAuth settings.

    Args:
        base_url: Base URL for the server
        oauth_url: OAuth provider URL
        oauth_client: OAuth client ID
        oauth_redirect_uri: Override redirect URI
        scope: OAuth scopes to request

    Returns:
        Configured OAuthConfig

    Example:
        ```python
        config = create_oauth_config_from_base_url(
            base_url="http://localhost:8000",
            oauth_url="https://auth.example.com/auth/realms/main",
            oauth_client="my-app"
        )
        ```
    """
    # Determine redirect URI
    if oauth_redirect_uri:
        redirect_uri = oauth_redirect_uri
    else:
        # Use 127.0.0.1 instead of localhost for better OAuth provider compatibility
        if "localhost" in base_url:
            normalized_url = base_url.replace("localhost", "127.0.0.1")
        else:
            normalized_url = base_url
        redirect_uri = f"{normalized_url}/oauth/callback"

    return OAuthConfig(
        oauth_url=oauth_url,
        client_id=oauth_client,
        redirect_uri=redirect_uri,
        scope=scope
    )


# Pre-configured OAuth provider configs for common use cases
OAUTH_PROVIDER_CONFIGS = {
    "ocm-cli": {
        "oauth_url": "https://sso.redhat.com/auth/realms/redhat-external",
        "client_id": "ocm-cli",
        "scope": "openid profile email"
    },
    "cloud-services": {
        "oauth_url": "https://sso.redhat.com/auth/realms/redhat-external",
        "client_id": "cloud-services",
        "scope": "openid profile email"
    },
    # Stage environment
    "ocm-cli-stage": {
        "oauth_url": "https://sso.stage.redhat.com/auth/realms/redhat-external",
        "client_id": "ocm-cli",
        "scope": "openid profile email"
    }
}


def get_oauth_provider_config(
    config_name: str,
    redirect_uri: str
) -> OAuthConfig:
    """Get pre-configured OAuth provider configuration.

    Args:
        config_name: Configuration name ("ocm-cli", "cloud-services", "ocm-cli-stage")
        redirect_uri: Your application's OAuth callback URL

    Returns:
        Pre-configured OAuthConfig for the specified provider

    Raises:
        ValueError: If config_name is not recognized

    Example:
        ```python
        # For Red Hat SSO
        config = get_oauth_provider_config("ocm-cli", "http://localhost:8000/oauth/callback")
        ```
    """
    if config_name not in OAUTH_PROVIDER_CONFIGS:
        available = list(OAUTH_PROVIDER_CONFIGS.keys())
        raise ValueError(f"Unknown OAuth provider config: {config_name}. Available: {available}")

    config_data = OAUTH_PROVIDER_CONFIGS[config_name]
    return OAuthConfig(
        oauth_url=config_data["oauth_url"],
        client_id=config_data["client_id"],
        redirect_uri=redirect_uri,
        scope=config_data["scope"]
    )


# Legacy aliases for backward compatibility
def create_assisted_service_oauth_config(
    self_url: str,
    oauth_url: str = "https://sso.redhat.com/auth/realms/redhat-external",
    oauth_client: str = "ocm-cli",
    oauth_redirect_uri: Optional[str] = None,
    scope: str = "openid profile email"
) -> OAuthConfig:
    """Legacy function - use create_oauth_config_from_base_url instead."""
    return create_oauth_config_from_base_url(
        base_url=self_url,
        oauth_url=oauth_url,
        oauth_client=oauth_client,
        oauth_redirect_uri=oauth_redirect_uri,
        scope=scope
    )

def create_config_from_settings(settings) -> OAuthConfig:
    """Legacy function for settings-based config."""
    return create_oauth_config_from_base_url(
        base_url=settings.SELF_URL,
        oauth_url=settings.OAUTH_URL,
        oauth_client=settings.OAUTH_CLIENT,
        oauth_redirect_uri=getattr(settings, 'OAUTH_REDIRECT_URI', None)
    )

def get_red_hat_sso_config(config_name: str, redirect_uri: str) -> OAuthConfig:
    """Legacy function name - use get_oauth_provider_config instead."""
    return get_oauth_provider_config(config_name, redirect_uri)