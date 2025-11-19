"""Type-safe models for MCP OAuth flow."""

import json
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuthConfig:
    """OAuth configuration for MCP servers.

    Supports various OAuth providers with standard OpenID Connect endpoints.
    """

    oauth_url: str  # OAuth provider base URL (e.g., "https://sso.redhat.com/auth/realms/redhat-external")
    client_id: str  # OAuth client identifier (e.g., "ocm-cli", "cloud-services")
    redirect_uri: str  # OAuth callback URL (e.g., "http://localhost:8000/oauth/callback")
    scope: str = "openid profile email"  # OAuth scopes to request

    # Optional advanced configuration
    authorization_endpoint: Optional[str] = None  # Override auth endpoint
    token_endpoint: Optional[str] = None  # Override token endpoint

    @property
    def auth_endpoint(self) -> str:
        """Get the authorization endpoint URL."""
        if self.authorization_endpoint:
            return self.authorization_endpoint
        return f"{self.oauth_url}/protocol/openid-connect/auth"

    @property
    def token_endpoint_url(self) -> str:
        """Get the token endpoint URL."""
        if self.token_endpoint:
            return self.token_endpoint
        return f"{self.oauth_url}/protocol/openid-connect/token"

    @classmethod
    def for_keycloak(
        cls,
        redirect_uri: str,
        client_id: str,
        oauth_url: str,
        scope: str = "openid profile email"
    ) -> "OAuthConfig":
        """Create configuration for Keycloak-based OAuth providers.

        Example for Red Hat SSO:
            config = OAuthConfig.for_keycloak(
                redirect_uri="http://localhost:8000/oauth/callback",
                client_id="ocm-cli",
                oauth_url="https://sso.redhat.com/auth/realms/redhat-external"
            )

        Args:
            redirect_uri: Your application's OAuth callback URL
            client_id: OAuth client ID
            oauth_url: OAuth realm URL
            scope: OAuth scopes to request

        Returns:
            Configured OAuthConfig for Keycloak-based providers
        """
        return cls(
            oauth_url=oauth_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope
        )

    @classmethod
    def from_env_vars(
        cls,
        oauth_url_env: str = "OAUTH_URL",
        client_id_env: str = "OAUTH_CLIENT",
        redirect_uri_env: str = "OAUTH_REDIRECT_URI",
        scope_env: str = "OAUTH_SCOPE"
    ) -> "OAuthConfig":
        """Create configuration from environment variables.

        Args:
            oauth_url_env: Environment variable name for OAuth URL
            client_id_env: Environment variable name for client ID
            redirect_uri_env: Environment variable name for redirect URI
            scope_env: Environment variable name for scope

        Returns:
            Configured OAuthConfig from environment variables

        Raises:
            ValueError: If required environment variables are missing
        """
        import os

        oauth_url = os.getenv(oauth_url_env)
        client_id = os.getenv(client_id_env)
        redirect_uri = os.getenv(redirect_uri_env)
        scope = os.getenv(scope_env, "openid profile email")

        if not oauth_url:
            raise ValueError(f"Missing required environment variable: {oauth_url_env}")
        if not client_id:
            raise ValueError(f"Missing required environment variable: {client_id_env}")
        if not redirect_uri:
            raise ValueError(f"Missing required environment variable: {redirect_uri_env}")

        return cls(
            oauth_url=oauth_url,
            client_id=client_id,
            redirect_uri=redirect_uri,
            scope=scope
        )


@dataclass
class OAuthToken:
    """OAuth token with MCP-specific metadata."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

    # MCP-specific fields
    client_identifier: str = ""  # MCP client ID (user-agent + IP)
    created_at: float = 0.0

    def __post_init__(self):
        """Set creation timestamp."""
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def expires_at(self) -> Optional[float]:
        """Calculate expiration timestamp."""
        if self.expires_in is None:
            return None
        return self.created_at + self.expires_in

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired (with optional buffer)."""
        if self.expires_at is None:
            return False
        return time.time() >= (self.expires_at - buffer_seconds)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": self.scope,
            "client_identifier": self.client_identifier,
            "created_at": self.created_at,
        }

    @classmethod
    def from_authlib(cls, token_data: dict, client_identifier: str = "") -> "OAuthToken":
        """Create from authlib token response."""
        return cls(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope"),
            client_identifier=client_identifier,
        )


@dataclass
class MCPOAuthState:
    """MCP-specific OAuth state for CSRF protection."""

    client_identifier: str
    timestamp: float
    code_verifier: str  # PKCE code verifier

    def to_json(self) -> str:
        """Serialize to JSON for OAuth state parameter."""
        return json.dumps({
            "client_identifier": self.client_identifier,
            "timestamp": self.timestamp,
            "code_verifier": self.code_verifier,
        })

    @classmethod
    def from_json(cls, state_str: str) -> "MCPOAuthState":
        """Deserialize from OAuth state parameter."""
        try:
            data = json.loads(state_str)
            return cls(
                client_identifier=data["client_identifier"],
                timestamp=data["timestamp"],
                code_verifier=data["code_verifier"],
            )
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid OAuth state: {e}") from e

    def is_expired(self, max_age_seconds: int = 600) -> bool:
        """Check if state is too old (default: 10 minutes)."""
        return time.time() - self.timestamp > max_age_seconds