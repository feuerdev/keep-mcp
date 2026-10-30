import argparse
import os
import sys

# Ensure src/ is on sys.path
sys.path.insert(0, os.path.abspath("src"))
sys.path.insert(0, os.path.abspath("."))

try:
    from server.web import create_app, run_server
except ImportError:
    from src.server.web import create_app, run_server

default_transport = os.getenv("MCP_TRANSPORT", os.getenv("TRANSPORT", "sse")).lower()
app = create_app(transport=default_transport)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run keep-mcp HTTP/SSE server")
    parser.add_argument(
        "--transport",
        choices=["sse", "streamable-http", "http", "web"],
        default=default_transport,
        help="Transport type (sse, streamable-http, default: sse)",
    )
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Host to bind (default: 0.0.0.0 or HOST env var)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8080")),
        help="Port to bind (default: 8080 or PORT env var)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "info"),
        help="Log level for uvicorn (default: info)",
    )
    args = parser.parse_args()

    web_transport = "streamable-http" if args.transport == "streamable-http" else "sse"
    run_server(host=args.host, port=args.port, log_level=args.log_level, transport=web_transport)
