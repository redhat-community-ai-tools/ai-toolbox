"""Thread-safe token storage for MCP OAuth."""

import threading
import time
from typing import Dict, Optional

from .models import OAuthToken


class TokenStorage:
    """Thread-safe in-memory token storage for MCP clients."""

    def __init__(self):
        """Initialize token storage."""
        self._lock = threading.RLock()  # Re-entrant lock for thread safety
        self._tokens: Dict[str, OAuthToken] = {}  # client_identifier -> token

    def store_token(self, client_identifier: str, token: OAuthToken) -> None:
        """Store token for a client.

        Args:
            client_identifier: Unique client identifier
            token: OAuth token to store
        """
        with self._lock:
            # Update client identifier in token
            token.client_identifier = client_identifier
            self._tokens[client_identifier] = token

    def get_token(self, client_identifier: str) -> Optional[OAuthToken]:
        """Get token for a client.

        Args:
            client_identifier: Client identifier

        Returns:
            Token if found, None otherwise
        """
        with self._lock:
            return self._tokens.get(client_identifier)

    def get_access_token(self, client_identifier: str) -> Optional[str]:
        """Get access token string for a client.

        Args:
            client_identifier: Client identifier

        Returns:
            Access token if found and not expired, None otherwise
        """
        token = self.get_token(client_identifier)
        if token and not token.is_expired():
            return token.access_token
        return None

    def remove_token(self, client_identifier: str) -> bool:
        """Remove token for a client.

        Args:
            client_identifier: Client identifier

        Returns:
            True if token was removed, False if not found
        """
        with self._lock:
            return self._tokens.pop(client_identifier, None) is not None

    def cleanup_expired_tokens(self) -> int:
        """Remove all expired tokens.

        Returns:
            Number of tokens removed
        """
        with self._lock:
            current_time = time.time()
            expired_clients = [
                client_id
                for client_id, token in self._tokens.items()
                if token.is_expired()
            ]

            for client_id in expired_clients:
                del self._tokens[client_id]

            return len(expired_clients)

    def get_all_tokens(self) -> Dict[str, OAuthToken]:
        """Get copy of all stored tokens (for debugging/monitoring).

        Returns:
            Dictionary of client_identifier -> token
        """
        with self._lock:
            return self._tokens.copy()

    def get_token_count(self) -> int:
        """Get number of stored tokens.

        Returns:
            Token count
        """
        with self._lock:
            return len(self._tokens)

    def clear_all(self) -> None:
        """Clear all stored tokens."""
        with self._lock:
            self._tokens.clear()