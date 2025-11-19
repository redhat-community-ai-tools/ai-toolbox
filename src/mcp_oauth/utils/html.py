"""HTML utilities for OAuth flow."""


def get_success_html(is_mcp_flow: bool = True) -> str:
    """Generate OAuth success HTML page.

    Args:
        is_mcp_flow: Whether this is an MCP flow

    Returns:
        HTML content for success page
    """
    instructions_html = """
    <div class="instructions">
        <h3>Next Steps:</h3>
        <ol>
            <li>Close this browser window</li>
            <li>Return to your MCP client (Cursor/Copilot/etc.)</li>
            <li>Your MCP connection should now work automatically</li>
        </ol>
    </div>
    """ if is_mcp_flow else """
    <div class="instructions">
        <p>You can now close this window and return to your application.</p>
    </div>
    """

    auto_close_delay = "3000" if is_mcp_flow else "5000"

    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                    color: white;
                    margin: 0;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .success {{
                    color: #4CAF50;
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    color: #4CAF50;
                    margin: 20px 0;
                }}
                .instructions {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }}
                .countdown {{
                    font-size: 14px;
                    color: #ddd;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">🎉</div>
                <h1>Authentication Successful!</h1>
                <p>You have successfully authenticated with the MCP OAuth server.</p>
                {instructions_html}
                <div class="countdown">
                    This window will close automatically in <span id="countdown">5</span> seconds.
                </div>
            </div>
            <script>
                let countdownElement = document.getElementById('countdown');
                let seconds = Math.floor({auto_close_delay} / 1000);

                let interval = setInterval(() => {{
                    countdownElement.textContent = seconds;
                    seconds--;
                    if (seconds < 0) {{
                        clearInterval(interval);
                        window.close();
                    }}
                }}, 1000);
            </script>
        </body>
    </html>
    """


def get_error_html(error_message: str, details: str = "") -> str:
    """Generate OAuth error HTML page.

    Args:
        error_message: Main error message
        details: Additional error details

    Returns:
        HTML content for error page
    """
    details_html = f"<p><strong>Details:</strong> {details}</p>" if details else ""

    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Authentication Failed</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                    background: linear-gradient(135deg, #ff7b7b 0%, #d63031 100%);
                    color: white;
                    margin: 0;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 10px;
                    backdrop-filter: blur(10px);
                    max-width: 500px;
                    margin: 0 auto;
                }}
                .error {{
                    color: #ff4757;
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                h1 {{
                    color: #ff4757;
                    margin: 20px 0;
                }}
                .details {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 20px;
                    border-radius: 5px;
                    margin: 20px 0;
                    text-align: left;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">❌</div>
                <h1>Authentication Failed</h1>
                <p>{error_message}</p>
                {details_html}
                <p>You can close this window and try again.</p>
            </div>
        </body>
    </html>
    """