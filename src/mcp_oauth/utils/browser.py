"""Browser integration utilities for OAuth flow."""

import webbrowser
from typing import Optional


def open_browser_for_auth(auth_url: str, logger: Optional[object] = None) -> bool:
    """Open browser for OAuth authentication.

    Args:
        auth_url: OAuth authorization URL
        logger: Optional logger instance

    Returns:
        True if browser opened successfully, False otherwise
    """
    try:
        webbrowser.open(auth_url)
        if logger:
            logger.info(f"Opened browser for OAuth: {auth_url}")
        return True
    except Exception as e:
        if logger:
            logger.warning(f"Failed to open browser automatically: {e}")
        return False