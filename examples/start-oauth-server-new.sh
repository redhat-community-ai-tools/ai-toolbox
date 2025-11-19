#!/bin/bash
set -e

echo "Starting Assisted Service MCP Server with mcp-oauth Library..."
echo

# Load OAuth configuration
if [ -f oauth-config.env ]; then
    export $(grep -v '^#' oauth-config.env | xargs)
elif [ -f ../oauth-config.env ]; then
    export $(grep -v '^#' ../oauth-config.env | xargs)
else
    echo "Error: oauth-config.env not found!"
    echo "Expected locations:"
    echo "  - ./oauth-config.env"
    echo "  - ../oauth-config.env"
    exit 1
fi

echo "✅ Configuration Loaded:"
echo "  OAuth Enabled: $OAUTH_ENABLED"
echo "  OAuth Client: $OAUTH_CLIENT"
echo "  OAuth URL: $OAUTH_URL"
echo "  Self URL: $SELF_URL"
echo "  Server: $MCP_HOST:$MCP_PORT"
echo "  Transport: $TRANSPORT"
echo

echo "🔗 OAuth Endpoints (with mcp-oauth library):"
echo "  Callback: $SELF_URL/oauth/callback"
echo "  Status: $SELF_URL/status"
echo "  MCP: $SELF_URL/mcp"
echo

echo "📋 MCP Client Configuration:"
echo "  Add this to your Cursor MCP settings:"
echo "  {"
echo "    \"assisted-local-oauth\": {"
echo "      \"transport\": \"streamable-http\","
echo "      \"url\": \"$SELF_URL/mcp\""
echo "    }"
echo "  }"
echo

echo "🔄 OAuth Flow (using mcp-oauth library):"
echo "  1. Cursor connects -> OAuth flow starts automatically"
echo "  2. Browser opens for Red Hat SSO authentication (ocm-cli)"
echo "  3. After authentication, connection proceeds with OAuth token"
echo "  4. Subsequent connections use cached/refreshed tokens"
echo "  5. Library handles PKCE, token refresh, and thread-safety"
echo

echo "🚀 Starting MCP server with OAuth library..."
echo "   Library: mcp-oauth v0.1.0"
echo "   Using: authlib (standards-compliant OAuth)"
echo "   Security: PKCE + state parameter + token refresh"
echo

echo "Press Ctrl+C to stop"
echo

# Choose which example to run
if [ "$1" = "migration" ]; then
    echo "Running migration example..."
    python examples/assisted_service_migration.py
elif [ "$1" = "basic" ]; then
    echo "Running basic example..."
    python examples/basic_mcp_server.py
else
    echo "Running assisted-service migration example..."
    echo "Use: $0 basic    - for basic example"
    echo "Use: $0 migration - for migration example"
    python examples/assisted_service_migration.py
fi