"""Basic MCP server example with OAuth authentication."""

import uvicorn
from fastapi import FastAPI, Request
from mcp_oauth import MCPOAuthClient, OAuthConfig
from mcp_oauth.integrations.fastapi import MCPOAuthMiddleware, oauth_callback_handler

# Create FastAPI app
app = FastAPI(title="MCP OAuth Example", version="0.1.0")

# OAuth configuration - Multiple ways to configure

# Method 1: Using OAuth provider preset (Red Hat SSO example)
from mcp_oauth import get_oauth_provider_config
oauth_config = get_oauth_provider_config(
    config_name="ocm-cli",  # Red Hat SSO ocm-cli client
    redirect_uri="http://127.0.0.1:8000/oauth/callback"
)

# Method 2: Manual configuration (same result)
# oauth_config = OAuthConfig(
#     oauth_url="https://sso.redhat.com/auth/realms/redhat-external",
#     client_id="ocm-cli",  # Same as assisted-service-mcp uses
#     redirect_uri="http://127.0.0.1:8000/oauth/callback",  # Note: 127.0.0.1 for better OAuth provider compatibility
#     scope="openid profile email"
# )

# Method 3: From environment variables
# oauth_config = OAuthConfig.from_env_vars()

# Method 4: Keycloak-based provider factory method
# oauth_config = OAuthConfig.for_keycloak(
#     redirect_uri="http://127.0.0.1:8000/oauth/callback",
#     client_id="ocm-cli",
#     oauth_url="https://sso.redhat.com/auth/realms/redhat-external"
# )

# Create OAuth client and middleware
oauth_client = MCPOAuthClient(oauth_config)
oauth_middleware = MCPOAuthMiddleware(oauth_client)


@app.middleware("http")
async def add_oauth_middleware(request: Request, call_next):
    """Add OAuth middleware to all requests."""
    return await oauth_middleware(request, call_next)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "MCP OAuth Example Server", "version": "0.1.0"}


@app.get("/oauth/callback")
async def handle_oauth_callback(request: Request):
    """Handle OAuth callback."""
    return await oauth_callback_handler(oauth_client, request)


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP endpoint that requires authentication.

    This endpoint will automatically trigger OAuth flow if the client
    is not authenticated. The middleware will:
    1. Detect MCP request without auth
    2. Open browser for user authentication
    3. Wait for OAuth completion
    4. Add Authorization header to the request
    """
    # Check if we have authentication
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return {"error": "No authentication provided"}

    return {
        "status": "authenticated",
        "message": "Successfully authenticated via OAuth!",
        "auth_method": "oauth",
        "token_type": "Bearer"
    }


@app.get("/status")
async def status():
    """Server status endpoint."""
    token_count = oauth_client.storage.get_token_count()
    return {
        "status": "healthy",
        "oauth_enabled": True,
        "active_tokens": token_count,
        "oauth_url": oauth_config.oauth_url,
        "client_id": oauth_config.client_id,
    }


if __name__ == "__main__":
    print("🚀 Starting MCP OAuth Example Server...")
    print(f"📋 Configuration:")
    print(f"   OAuth URL: {oauth_config.oauth_url}")
    print(f"   Client ID: {oauth_config.client_id}")
    print(f"   Redirect URI: {oauth_config.redirect_uri}")
    print(f"   Scope: {oauth_config.scope}")
    print(f"\n🌐 Server will be available at: http://127.0.0.1:8000")
    print(f"🧪 Test the MCP endpoint at: http://127.0.0.1:8000/mcp")
    print(f"📊 Check server status at: http://127.0.0.1:8000/status")
    print(f"\n💡 This example shows OAuth integration with various providers:")
    print(f"   - Works with Red Hat SSO using the same settings as assisted-service-mcp")

    uvicorn.run(
        "basic_mcp_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )