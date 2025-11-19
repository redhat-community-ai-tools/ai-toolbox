"""Core OAuth client using authlib for MCP servers."""

import secrets
import time
import urllib.parse
from typing import Optional, Tuple

from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from .models import MCPOAuthState, OAuthConfig, OAuthToken
from .storage import TokenStorage


class MCPOAuthClient:
    """OAuth 2.1 + PKCE client for MCP servers using authlib."""

    def __init__(self, config: OAuthConfig, token_storage: Optional[TokenStorage] = None):
        """Initialize OAuth client.

        Args:
            config: OAuth configuration
            token_storage: Optional token storage (creates default if None)
        """
        self.config = config
        self.storage = token_storage or TokenStorage()

        # OAuth client using authlib
        self._oauth_client = AsyncOAuth2Client(
            client_id=config.client_id,
            redirect_uri=config.redirect_uri,
        )

        # Track pending OAuth states for CSRF protection
        self._pending_states: dict[str, MCPOAuthState] = {}

    def create_authorization_url(self, client_identifier: str) -> Tuple[str, str]:
        """Create OAuth authorization URL with PKCE.

        Args:
            client_identifier: Unique identifier for the MCP client

        Returns:
            Tuple of (authorization_url, state_json)
        """
        # Generate PKCE challenge
        code_verifier = secrets.token_urlsafe(32)
        code_challenge = create_s256_code_challenge(code_verifier)

        # Create state for CSRF protection
        state = MCPOAuthState(
            client_identifier=client_identifier,
            timestamp=time.time(),
            code_verifier=code_verifier,
        )
        state_json = state.to_json()

        # Store state for validation
        self._pending_states[state_json] = state

        # Build authorization URL
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": self.config.scope,
            "state": state_json,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }

        authorization_url = f"{self.config.auth_endpoint}?{urllib.parse.urlencode(params)}"

        return authorization_url, state_json

    async def exchange_code_for_token(self, code: str, state_json: str) -> OAuthToken:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth provider
            state_json: OAuth state parameter (JSON)

        Returns:
            OAuth token

        Raises:
            ValueError: If state is invalid, expired, or code exchange fails
        """
        # Validate and retrieve state
        if state_json not in self._pending_states:
            raise ValueError("Invalid or unknown OAuth state")

        state = self._pending_states.pop(state_json)

        if state.is_expired():
            raise ValueError("OAuth state expired")

        try:
            # Use authlib to exchange code for token
            token_endpoint = self.config.token_endpoint_url

            # Prepare authorization response URL for authlib
            callback_url = f"{self.config.redirect_uri}?code={code}&state={state_json}"

            # Exchange code for token using authlib
            token_data = await self._oauth_client.fetch_token(
                token_endpoint,
                authorization_response=callback_url,
                code_verifier=state.code_verifier,
            )

            # Convert to our token model
            token = OAuthToken.from_authlib(token_data, state.client_identifier)

            # Store token
            self.storage.store_token(state.client_identifier, token)

            return token

        except Exception as e:
            raise ValueError(f"Failed to exchange code for token: {e}") from e

    async def get_access_token(self, client_identifier: str) -> Optional[str]:
        """Get valid access token for client, refreshing if needed.

        Args:
            client_identifier: MCP client identifier

        Returns:
            Access token if available and valid, None otherwise
        """
        token = self.storage.get_token(client_identifier)
        if not token:
            return None

        # Check if token needs refresh
        if token.is_expired():
            if token.refresh_token:
                refreshed_token = await self._refresh_token(token)
                if refreshed_token:
                    self.storage.store_token(client_identifier, refreshed_token)
                    return refreshed_token.access_token

            # Remove expired token if refresh failed or no refresh token
            self.storage.remove_token(client_identifier)
            return None

        return token.access_token

    async def _refresh_token(self, token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh access token using refresh token.

        Args:
            token: Token to refresh

        Returns:
            New token if refresh successful, None otherwise
        """
        if not token.refresh_token:
            return None

        try:
            token_endpoint = self.config.token_endpoint_url

            # Use authlib to refresh token
            refreshed_data = await self._oauth_client.refresh_token(
                token_endpoint,
                refresh_token=token.refresh_token,
            )

            # Create new token
            return OAuthToken.from_authlib(refreshed_data, token.client_identifier)

        except Exception:
            return None

    def cleanup_expired_states(self, max_age_seconds: int = 600) -> int:
        """Clean up expired OAuth states.

        Args:
            max_age_seconds: Maximum age for states (default: 10 minutes)

        Returns:
            Number of states cleaned up
        """
        current_time = time.time()
        expired_states = [
            state_json
            for state_json, state in self._pending_states.items()
            if current_time - state.timestamp > max_age_seconds
        ]

        for state_json in expired_states:
            del self._pending_states[state_json]

        return len(expired_states)

    def get_client_identifier(self, user_agent: str = "", client_ip: str = "") -> str:
        """Generate client identifier from request info.

        Args:
            user_agent: User agent string
            client_ip: Client IP address

        Returns:
            Unique client identifier
        """
        return f"{user_agent or 'unknown'}_{client_ip or 'unknown'}"