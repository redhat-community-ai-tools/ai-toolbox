"""Utility functions for MCP OAuth."""

from .browser import open_browser_for_auth
from .html import get_error_html, get_success_html

__all__ = [
    "open_browser_for_auth",
    "get_success_html",
    "get_error_html",
]