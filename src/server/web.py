"""
Web server entrypoint for keep-mcp running over SSE / HTTP.
Suitable for containerized deployment (e.g., Google Cloud Run, Docker).
"""

import argparse
import importlib.metadata
import os
from urllib.parse import parse_qs

from dotenv import load_dotenv
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import uvicorn

# Load local .env if present
load_dotenv()

from .cli import mcp

try:
    __version__ = importlib.metadata.version("keep-mcp")
except Exception:
    __version__ = "0.3.0"


class ApiKeyAuthMiddleware:
    """
    Pure ASGI middleware that enforces API key authentication on MCP routes,
    while permitting unauthenticated health checks on /, /health, and /healthz.
    """

    def __init__(self, app: ASGIApp, api_key: str | None = None):
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "http":
            path = scope.get("path", "")

            # Public health endpoints for container health checks
            if path in ("/", "/healthz", "/health"):
                if path == "/" and scope.get("method") == "GET":
                    resp = JSONResponse(
                        {"status": "ok", "service": "keep-mcp", "version": __version__}
                    )
                else:
                    resp = PlainTextResponse("OK")
                await resp(scope, receive, send)
                return

            # API key validation if configured
            if self.api_key:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode("utf-8", "ignore")
                x_api_key = headers.get(b"x-api-key", b"").decode("utf-8", "ignore")
                query_string = scope.get("query_string", b"").decode("utf-8", "ignore")
                query_params = parse_qs(query_string)

                provided = None
                if auth_header.lower().startswith("bearer "):
                    provided = auth_header[7:].strip()
                elif x_api_key:
                    provided = x_api_key.strip()
                elif "token" in query_params:
                    provided = query_params["token"][0].strip()
                elif "api_key" in query_params:
                    provided = query_params["api_key"][0].strip()

                if provided != self.api_key:
                    resp = JSONResponse(
                        {"error": "Unauthorized", "detail": "Invalid or missing MCP API key"},
                        status_code=401,
                    )
                    await resp(scope, receive, send)
                    return

        await self.app(scope, receive, send)


def create_app(api_key: str | None = None, transport: str = "sse") -> ASGIApp:
    """
    Construct the ASGI application for SSE / Streamable HTTP MCP transport with health checks
    and optional API key authentication.
    """
    if api_key is None:
        api_key = os.getenv("MCP_API_KEY")

    # In MCP 2.x, configure transport security to avoid localhost DNS rebinding restrictions
    # when hosted on 0.0.0.0 or container environments
    try:
        from mcp.server.transport_security import TransportSecuritySettings

        security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
    except Exception:
        security = None

    if transport == "streamable-http":
        if security is not None:
            base_app = mcp.streamable_http_app(transport_security=security)
        else:
            try:
                base_app = mcp.streamable_http_app(host="0.0.0.0")
            except TypeError:
                base_app = mcp.streamable_http_app()
    else:
        if security is not None:
            base_app = mcp.sse_app(transport_security=security)
        else:
            try:
                base_app = mcp.sse_app(host="0.0.0.0")
            except TypeError:
                base_app = mcp.sse_app()

    return ApiKeyAuthMiddleware(base_app, api_key=api_key)


def run_server(host: str = "0.0.0.0", port: int = 8080, log_level: str = "info", transport: str = "sse"):
    """Run the web server with uvicorn."""
    app = create_app(transport=transport)
    uvicorn.run(app, host=host, port=port, log_level=log_level)


def main():
    parser = argparse.ArgumentParser(description="keep-mcp SSE / HTTP Server")
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host address to bind (default: 0.0.0.0 or HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port number to bind (default: 8080 or PORT env var)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        help="Log level for uvicorn (default: info)",
    )

    args = parser.parse_args()
    run_server(host=args.host, port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
