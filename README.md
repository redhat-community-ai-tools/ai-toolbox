# MCP OAuth

A lightweight OAuth 2.1 + PKCE library specifically designed for MCP (Model Context Protocol) servers. Built on top of [authlib](https://authlib.org/) for security and standards compliance.

## Features

- **Standards Compliant**: OAuth 2.1 with PKCE (RFC 7636) support
- **MCP Optimized**: Designed specifically for MCP server authentication flows
- **FastAPI Integration**: Ready-to-use middleware for FastAPI applications
- **Thread-Safe**: Concurrent token storage and management
- **Automatic Refresh**: Transparent token refresh using refresh tokens
- **Browser Integration**: Automatic browser opening for user authentication

## Installation

```bash
pip install mcp-oauth
```

## Quick Start

### Basic Setup

```python
from mcp_oauth import MCPOAuthClient, OAuthConfig, get_oauth_provider_config

# Option 1: Pre-configured provider (Red Hat SSO example)
config = get_oauth_provider_config(
    config_name="ocm-cli",
    redirect_uri="http://127.0.0.1:8000/oauth/callback"
)

# Option 2: Manual configuration
# config = OAuthConfig(
#     oauth_url="https://auth.example.com/auth/realms/main",
#     client_id="my-app",
#     redirect_uri="http://127.0.0.1:8000/oauth/callback",
#     scope="openid profile email"
# )

# Option 3: Keycloak-based provider
# config = OAuthConfig.for_keycloak(
#     redirect_uri="http://127.0.0.1:8000/oauth/callback",
#     client_id="ocm-cli",
#     oauth_url="https://sso.redhat.com/auth/realms/redhat-external"
# )

# Option 4: From environment variables
# config = OAuthConfig.from_env_vars()

# Create OAuth client
oauth_client = MCPOAuthClient(config)
```

### FastAPI Integration

```python
from fastapi import FastAPI, Request
from mcp_oauth.integrations.fastapi import MCPOAuthMiddleware, oauth_callback_handler

app = FastAPI()

# Add OAuth middleware
oauth_middleware = MCPOAuthMiddleware(oauth_client)

@app.middleware("http")
async def oauth_middleware_handler(request: Request, call_next):
    return await oauth_middleware(request, call_next)

# Add OAuth callback endpoint
@app.get("/oauth/callback")
async def oauth_callback(request: Request):
    return await oauth_callback_handler(oauth_client, request)
```

### Manual OAuth Flow

```python
# Create authorization URL
client_id = "some-unique-client-identifier"
auth_url, state = oauth_client.create_authorization_url(client_id)

print(f"Visit: {auth_url}")

# After user authentication, exchange code for token
code = "authorization-code-from-callback"
token = await oauth_client.exchange_code_for_token(code, state)

print(f"Access token: {token.access_token}")
```

## Configuration

### Configuration Options

#### OAuthConfig Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `oauth_url` | `str` | OAuth provider base URL | `https://auth.example.com/auth/realms/main` |
| `client_id` | `str` | OAuth client identifier | `my-app` |
| `redirect_uri` | `str` | Callback URL for OAuth flow | `http://127.0.0.1:8000/oauth/callback` |
| `scope` | `str` | OAuth scopes to request | `openid profile email` |
| `authorization_endpoint` | `str` (optional) | Override authorization endpoint | `https://custom.sso.com/auth` |
| `token_endpoint` | `str` (optional) | Override token endpoint | `https://custom.sso.com/token` |

#### OAuth Provider Presets

```python
from mcp_oauth import get_oauth_provider_config

# Red Hat SSO - Production OCM CLI
config = get_oauth_provider_config("ocm-cli", redirect_uri)

# Red Hat SSO - Production Cloud Services
config = get_oauth_provider_config("cloud-services", redirect_uri)

# Red Hat SSO - Stage Environment
config = get_oauth_provider_config("ocm-cli-stage", redirect_uri)
```

#### Factory Methods

```python
# Keycloak-based provider (Red Hat SSO example)
config = OAuthConfig.for_keycloak(
    redirect_uri="http://127.0.0.1:8000/oauth/callback",
    client_id="ocm-cli",
    oauth_url="https://sso.redhat.com/auth/realms/redhat-external"
)

# From environment variables
config = OAuthConfig.from_env_vars(
    oauth_url_env="OAUTH_URL",      # Default
    client_id_env="OAUTH_CLIENT",   # Default
    redirect_uri_env="OAUTH_REDIRECT_URI",  # Default
    scope_env="OAUTH_SCOPE"         # Default
)
```

#### Server Integration

```python
from mcp_oauth import create_oauth_config_from_base_url

# Create config from server base URL
config = create_oauth_config_from_base_url(
    base_url="http://localhost:8000",
    oauth_url="https://auth.example.com/auth/realms/main",
    oauth_client="my-app"
    # oauth_redirect_uri=None  # Auto-constructs /oauth/callback endpoint
)
```

### Environment Variables

You can also configure using environment variables (same as assisted-service-mcp):

```bash
export OAUTH_URL="https://auth.example.com/auth/realms/main"
export OAUTH_CLIENT="my-app"
export OAUTH_REDIRECT_URI="http://127.0.0.1:8000/oauth/callback"
export OAUTH_SCOPE="openid profile email"
```

Then load with:
```python
config = OAuthConfig.from_env_vars(client_id_env="OAUTH_CLIENT")
# or
config = create_oauth_config_from_base_url(
    base_url="http://localhost:8000",
    oauth_url=os.getenv("OAUTH_URL"),
    oauth_client=os.getenv("OAUTH_CLIENT")
)
```

## Advanced Usage

### Custom Token Storage

```python
from mcp_oauth.core.storage import TokenStorage

# Create custom storage (e.g., with Redis backend)
class RedisTokenStorage(TokenStorage):
    def __init__(self, redis_client):
        super().__init__()
        self.redis = redis_client

    def store_token(self, client_identifier: str, token: OAuthToken):
        # Store in Redis
        pass

# Use with OAuth client
storage = RedisTokenStorage(redis_client)
oauth_client = MCPOAuthClient(config, token_storage=storage)
```

### Token Management

```python
# Get valid access token (auto-refreshes if needed)
access_token = await oauth_client.get_access_token("client-id")

# Manual token refresh
token = oauth_client.storage.get_token("client-id")
if token and token.refresh_token:
    refreshed_token = await oauth_client._refresh_token(token)
```

### Cleanup

```python
# Clean up expired tokens
removed_count = oauth_client.storage.cleanup_expired_tokens()

# Clean up expired OAuth states
removed_states = oauth_client.cleanup_expired_states()
```

## Security Features

- **PKCE (Proof Key for Code Exchange)**: Enhanced OAuth security using SHA256 code challenges
- **State Parameter**: CSRF protection using cryptographically secure random states
- **Token Expiration**: Automatic token expiration handling with configurable buffer time
- **Thread Safety**: All token operations are thread-safe using re-entrant locks

## Integration Examples

### Basic MCP Server

```python
from fastapi import FastAPI
from mcp_oauth import get_oauth_provider_config, MCPOAuthClient
from mcp_oauth.integrations.fastapi import MCPOAuthMiddleware, oauth_callback_handler

app = FastAPI()

# OAuth configuration (Red Hat SSO example)
oauth_config = get_oauth_provider_config(
    config_name="ocm-cli",  # Red Hat's OCM CLI client
    redirect_uri="http://127.0.0.1:8000/oauth/callback"
)

# Create OAuth client and middleware
oauth_client = MCPOAuthClient(oauth_config)
oauth_middleware = MCPOAuthMiddleware(oauth_client)

# Add middleware
@app.middleware("http")
async def add_oauth_middleware(request, call_next):
    return await oauth_middleware(request, call_next)

# OAuth endpoints
@app.get("/oauth/callback")
async def handle_oauth_callback(request):
    return await oauth_callback_handler(oauth_client, request)

# Your MCP endpoints
@app.post("/mcp")
async def mcp_endpoint(request):
    # This will automatically trigger OAuth if needed
    # The Authorization header will be added by middleware
    return {"status": "authenticated"}
```

### Generic Server Integration

```python
from mcp_oauth import create_oauth_config_from_base_url, MCPOAuthClient
from mcp_oauth.integrations.fastapi import MCPOAuthMiddleware, oauth_callback_handler
import os

app = FastAPI()

# Create OAuth config from environment or settings
oauth_enabled = os.getenv("OAUTH_ENABLED", "false").lower() == "true"

if oauth_enabled:
    oauth_config = create_oauth_config_from_base_url(
        base_url=os.getenv("SERVER_URL", "http://localhost:8000"),
        oauth_url=os.getenv("OAUTH_URL"),
        oauth_client=os.getenv("OAUTH_CLIENT")
    )
    oauth_client = MCPOAuthClient(oauth_config)
    oauth_middleware = MCPOAuthMiddleware(oauth_client)

@app.middleware("http")
async def oauth_middleware_handler(request, call_next):
    if oauth_enabled:
        return await oauth_middleware(request, call_next)
    return await call_next(request)

@app.get("/oauth/callback")
async def oauth_callback(request):
    return await oauth_callback_handler(oauth_client, request)

# Example authentication priority logic
async def get_access_token_with_priority(request):
    # Priority 1: Bearer token from header
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    # Priority 2: OAuth flow
    if oauth_enabled:
        client_id = oauth_client.get_client_identifier(
            user_agent=request.headers.get("user-agent", ""),
            client_ip=getattr(request.client, "host", "") if request.client else ""
        )
        return await oauth_client.get_access_token(client_id)

    # Priority 3: Other authentication methods
    return None
```

## Error Handling

```python
try:
    token = await oauth_client.exchange_code_for_token(code, state)
except ValueError as e:
    if "expired" in str(e):
        # Handle expired state
        pass
    elif "invalid" in str(e):
        # Handle invalid state/code
        pass
```

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run linting
black src/ tests/
mypy src/
pylint src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Credits

Built on top of [authlib](https://authlib.org/) for OAuth implementation.
Designed for the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) ecosystem.