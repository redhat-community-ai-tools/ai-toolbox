"""FastAPI integration for MCP OAuth middleware."""

import asyncio
from typing import Callable, Dict, Any, Optional

from fastapi import Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.requests import Request as StarletteRequest

from ..core.client import MCPOAuthClient
from ..core.models import OAuthConfig
from ..utils.browser import open_browser_for_auth
from ..utils.html import get_success_html


class MCPOAuthMiddleware:
    """FastAPI middleware for automatic MCP OAuth flow."""

    def __init__(self, oauth_client: MCPOAuthClient):
        """Initialize middleware.

        Args:
            oauth_client: Configured OAuth client
        """
        self.oauth_client = oauth_client
        self.pending_auth_sessions: Dict[str, Dict[str, Any]] = {}

    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request through OAuth middleware.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from handler or OAuth flow
        """
        # Check if this request needs OAuth authentication
        if not self._should_handle_oauth(request):
            return await call_next(request)

        client_identifier = self._get_client_identifier(request)

        # Try to get existing valid token
        access_token = await self.oauth_client.get_access_token(client_identifier)
        if access_token:
            return await self._create_authenticated_request(request, call_next, access_token)

        # Check if OAuth flow is already in progress
        if self._has_pending_auth(client_identifier):
            return await self._wait_for_oauth_completion(request, call_next, client_identifier)

        # Start new OAuth flow
        return await self._start_oauth_flow(request, call_next, client_identifier)

    def _should_handle_oauth(self, request: Request) -> bool:
        """Check if this request should trigger OAuth flow.

        Args:
            request: FastAPI request

        Returns:
            True if OAuth should be triggered
        """
        # Check if it's an MCP request
        is_mcp_request = (
            request.url.path.startswith("/mcp")
            or "mcp" in request.headers.get("user-agent", "").lower()
            or request.headers.get("content-type", "").startswith("application/json")
        )

        # Check if authentication is missing
        has_auth = (
            request.headers.get("authorization")
            or request.headers.get("x-oauth-token-id")
        )

        return is_mcp_request and not has_auth

    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier.

        Args:
            request: FastAPI request

        Returns:
            Client identifier string
        """
        user_agent = request.headers.get("user-agent", "")
        client_ip = getattr(request.client, "host", "") if request.client else ""
        return self.oauth_client.get_client_identifier(user_agent, client_ip)

    def _has_pending_auth(self, client_identifier: str) -> bool:
        """Check if client has pending authentication.

        Args:
            client_identifier: Client identifier

        Returns:
            True if auth is pending
        """
        return any(
            session.get("client_identifier") == client_identifier
            for session in self.pending_auth_sessions.values()
        )

    async def _start_oauth_flow(
        self, request: Request, call_next: Callable, client_identifier: str
    ) -> Response:
        """Start OAuth flow for client.

        Args:
            request: FastAPI request
            call_next: Next handler
            client_identifier: Client identifier

        Returns:
            Response (success after OAuth or timeout)
        """
        # Create authorization URL
        auth_url, state_json = self.oauth_client.create_authorization_url(client_identifier)

        # Store session info
        session_id = f"oauth_{len(self.pending_auth_sessions)}"
        self.pending_auth_sessions[session_id] = {
            "client_identifier": client_identifier,
            "state": state_json,
            "auth_url": auth_url,
            "timestamp": asyncio.get_event_loop().time(),
        }

        # Open browser automatically
        open_browser_for_auth(auth_url)

        # Wait for OAuth completion
        return await self._wait_for_oauth_completion(request, call_next, client_identifier)

    async def _wait_for_oauth_completion(
        self, request: Request, call_next: Callable, client_identifier: str
    ) -> Response:
        """Wait for OAuth completion.

        Args:
            request: FastAPI request
            call_next: Next handler
            client_identifier: Client identifier

        Returns:
            Authenticated response or timeout error
        """
        max_wait_time = 60  # 1 minute
        poll_interval = 1   # 1 second
        waited_time = 0

        while waited_time < max_wait_time:
            await asyncio.sleep(poll_interval)
            waited_time += poll_interval

            # Check if OAuth completed
            access_token = await self.oauth_client.get_access_token(client_identifier)
            if access_token:
                # Clean up sessions
                self._cleanup_client_sessions(client_identifier)
                return await self._create_authenticated_request(request, call_next, access_token)

        # OAuth timed out
        auth_url = self._get_auth_url_for_client(client_identifier)
        self._cleanup_client_sessions(client_identifier)

        return JSONResponse(
            {
                "type": "oauth_timeout",
                "message": "OAuth authentication timed out",
                "auth_url": auth_url,
                "instructions": [
                    "1. Authentication timed out",
                    "2. You can authenticate manually at:",
                    f"   {auth_url}",
                    "3. Or reconnect to retry automatically",
                ],
            },
            status_code=401,
        )

    def _get_auth_url_for_client(self, client_identifier: str) -> Optional[str]:
        """Get auth URL for client from pending sessions."""
        for session in self.pending_auth_sessions.values():
            if session.get("client_identifier") == client_identifier:
                return session.get("auth_url")
        return None

    def _cleanup_client_sessions(self, client_identifier: str) -> None:
        """Clean up pending sessions for client."""
        sessions_to_remove = [
            session_id
            for session_id, session in self.pending_auth_sessions.items()
            if session.get("client_identifier") == client_identifier
        ]
        for session_id in sessions_to_remove:
            del self.pending_auth_sessions[session_id]

    async def _create_authenticated_request(
        self, request: Request, call_next: Callable, access_token: str
    ) -> Response:
        """Create request with authentication header.

        Args:
            request: Original request
            call_next: Next handler
            access_token: OAuth access token

        Returns:
            Response from handler
        """
        # Modify request headers
        new_headers = list(request.scope.get("headers", []))
        # Remove existing authorization header
        new_headers = [(k, v) for k, v in new_headers if k.lower() != b"authorization"]
        # Add OAuth token
        new_headers.append((b"authorization", f"Bearer {access_token}".encode()))

        # Create new request with updated headers
        new_scope = dict(request.scope)
        new_scope["headers"] = new_headers
        new_request = StarletteRequest(new_scope, request.receive)

        return await call_next(new_request)

    def cleanup_expired_sessions(self, max_age_seconds: int = 600) -> None:
        """Clean up expired auth sessions."""
        current_time = asyncio.get_event_loop().time()
        expired_sessions = [
            session_id
            for session_id, session in self.pending_auth_sessions.items()
            if current_time - session["timestamp"] > max_age_seconds
        ]

        for session_id in expired_sessions:
            del self.pending_auth_sessions[session_id]


async def oauth_callback_handler(oauth_client: MCPOAuthClient, request: Request) -> Response:
    """Handle OAuth callback.

    Args:
        oauth_client: OAuth client instance
        request: FastAPI request with callback parameters

    Returns:
        HTML response showing success or error
    """
    # Extract callback parameters
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    error = request.query_params.get("error")

    if error:
        return HTMLResponse(
            f"""
            <html>
                <body>
                    <h1>OAuth Authentication Failed</h1>
                    <p>Error: {error}</p>
                    <p>You can close this window.</p>
                </body>
            </html>
            """,
            status_code=400,
        )

    if not code or not state:
        return HTMLResponse(
            """
            <html>
                <body>
                    <h1>OAuth Authentication Failed</h1>
                    <p>Missing authorization code or state.</p>
                    <p>You can close this window.</p>
                </body>
            </html>
            """,
            status_code=400,
        )

    try:
        # Exchange code for token
        token = await oauth_client.exchange_code_for_token(code, state)

        # Show success page
        return HTMLResponse(content=get_success_html(is_mcp_flow=True))

    except ValueError as e:
        return HTMLResponse(
            f"""
            <html>
                <body>
                    <h1>OAuth Authentication Failed</h1>
                    <p>Failed to exchange authorization code for token.</p>
                    <p>Error: {str(e)}</p>
                    <p>You can close this window.</p>
                </body>
            </html>
            """,
            status_code=400,
        )


def create_oauth_middleware(config: OAuthConfig) -> MCPOAuthMiddleware:
    """Create configured OAuth middleware.

    Args:
        config: OAuth configuration

    Returns:
        Configured middleware instance
    """
    oauth_client = MCPOAuthClient(config)
    return MCPOAuthMiddleware(oauth_client)