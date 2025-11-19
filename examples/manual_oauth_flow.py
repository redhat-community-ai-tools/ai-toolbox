"""Manual OAuth flow example - demonstrates programmatic usage."""

import asyncio
from mcp_oauth import MCPOAuthClient, OAuthConfig
from mcp_oauth.utils.browser import open_browser_for_auth


async def manual_oauth_example():
    """Demonstrate manual OAuth flow without FastAPI."""

    print("🔐 MCP OAuth Manual Flow Example")
    print("=" * 40)

    # Configuration - using Keycloak-based provider (Red Hat SSO example)
    config = OAuthConfig.for_keycloak(
        redirect_uri="http://127.0.0.1:8000/oauth/callback",
        client_id="ocm-cli",  # Red Hat SSO client
        oauth_url="https://sso.redhat.com/auth/realms/redhat-external"
    )

    # Alternative: manual configuration
    # config = OAuthConfig(
    #     oauth_url="https://sso.redhat.com/auth/realms/redhat-external",
    #     client_id="ocm-cli",
    #     redirect_uri="http://127.0.0.1:8000/oauth/callback",
    #     scope="openid profile email"
    # )

    print(f"📋 Configuration:")
    print(f"   OAuth URL: {config.oauth_url}")
    print(f"   Client ID: {config.client_id}")
    print(f"   Redirect URI: {config.redirect_uri}")
    print(f"   Scope: {config.scope}")
    print()

    # Create OAuth client
    oauth_client = MCPOAuthClient(config)

    # Generate client identifier (in real usage, this comes from request)
    client_identifier = "manual_example_client"

    print(f"🆔 Client Identifier: {client_identifier}")
    print()

    # Step 1: Create authorization URL
    print("🔗 Step 1: Creating authorization URL...")
    auth_url, state = oauth_client.create_authorization_url(client_identifier)

    print(f"✅ Authorization URL created")
    print(f"   URL: {auth_url[:80]}...")
    print(f"   State: {state[:50]}...")
    print()

    # Step 2: Open browser (in real app, this would be automatic)
    print("🌐 Step 2: Opening browser for authentication...")
    browser_opened = open_browser_for_auth(auth_url)

    if browser_opened:
        print("✅ Browser opened successfully")
    else:
        print("⚠️  Could not open browser automatically")
        print(f"   Please visit: {auth_url}")

    print()
    print("👤 Please complete authentication in your browser...")
    print("   This example will wait for you to manually provide the callback info.")
    print()

    # Step 3: Simulate getting callback parameters
    # In a real application, these would come from the OAuth callback
    print("📥 Step 3: Simulating OAuth callback...")
    print("   (In real usage, this would be handled by your callback endpoint)")

    # For this example, we'll ask the user to provide the code
    print("\n🔄 After completing authentication, you should be redirected to:")
    print(f"   {config.redirect_uri}?code=AUTHORIZATION_CODE&state=STATE")
    print()
    print("📝 Please copy the 'code' parameter from the redirect URL:")

    try:
        # In a real scenario, this would come from the callback
        code = input("   Enter authorization code: ").strip()

        if not code:
            print("❌ No authorization code provided. Exiting.")
            return

        print(f"   Code received: {code[:20]}...")
        print()

        # Step 4: Exchange code for token
        print("🔄 Step 4: Exchanging authorization code for access token...")

        token = await oauth_client.exchange_code_for_token(code, state)

        print("✅ Token exchange successful!")
        print(f"   Access Token: {token.access_token[:30]}...")
        print(f"   Token Type: {token.token_type}")
        print(f"   Expires In: {token.expires_in} seconds")
        print(f"   Refresh Token: {'Yes' if token.refresh_token else 'No'}")
        print(f"   Scope: {token.scope}")
        print()

        # Step 5: Use the token
        print("🎯 Step 5: Retrieving stored access token...")

        stored_token = await oauth_client.get_access_token(client_identifier)

        if stored_token:
            print("✅ Access token retrieved successfully")
            print(f"   Token: {stored_token[:30]}...")
        else:
            print("❌ Failed to retrieve access token")

        print()

        # Step 6: Token info
        print("📊 Step 6: Token storage info...")
        token_count = oauth_client.storage.get_token_count()
        print(f"   Total stored tokens: {token_count}")

        # Show token details
        stored_token_obj = oauth_client.storage.get_token(client_identifier)
        if stored_token_obj:
            print(f"   Token expires at: {stored_token_obj.expires_at}")
            print(f"   Token is expired: {stored_token_obj.is_expired()}")

        print()
        print("🎉 OAuth flow completed successfully!")

    except KeyboardInterrupt:
        print("\n⚠️  Example cancelled by user")
    except ValueError as e:
        print(f"❌ OAuth error: {e}")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")

    finally:
        print("\n🧹 Cleaning up...")
        # Cleanup
        oauth_client.storage.clear_all()
        oauth_client.cleanup_expired_states()
        print("✅ Cleanup complete")


async def token_management_example():
    """Demonstrate token management features."""

    print("\n" + "=" * 50)
    print("🛠️  Token Management Example")
    print("=" * 50)

    config = OAuthConfig(
        oauth_url="https://sso.redhat.com/auth/realms/redhat-external",
        client_id="cloud-services",
        redirect_uri="http://localhost:8000/oauth/callback",
    )

    oauth_client = MCPOAuthClient(config)

    # Simulate storing some tokens
    from mcp_oauth.core.models import OAuthToken
    import time

    print("📝 Creating sample tokens...")

    # Create some sample tokens
    tokens = [
        OAuthToken(
            access_token=f"token_{i}",
            token_type="Bearer",
            expires_in=3600,
            client_identifier=f"client_{i}"
        )
        for i in range(3)
    ]

    # Store tokens
    for token in tokens:
        oauth_client.storage.store_token(token.client_identifier, token)

    print(f"✅ Stored {len(tokens)} tokens")
    print(f"   Token count: {oauth_client.storage.get_token_count()}")
    print()

    # Demonstrate retrieval
    print("🔍 Retrieving tokens...")
    for i in range(3):
        client_id = f"client_{i}"
        token = oauth_client.storage.get_token(client_id)
        if token:
            print(f"   {client_id}: {token.access_token} (expires: {token.is_expired()})")

    print()

    # Demonstrate cleanup
    print("🧹 Testing cleanup...")
    initial_count = oauth_client.storage.get_token_count()
    cleaned_up = oauth_client.storage.cleanup_expired_tokens()
    final_count = oauth_client.storage.get_token_count()

    print(f"   Initial tokens: {initial_count}")
    print(f"   Expired tokens removed: {cleaned_up}")
    print(f"   Final tokens: {final_count}")

    # Clear all for cleanup
    oauth_client.storage.clear_all()
    print("   All tokens cleared")


async def main():
    """Run all examples."""
    await manual_oauth_example()
    await token_management_example()
    print("\n✨ All examples completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Examples interrupted by user. Goodbye!")