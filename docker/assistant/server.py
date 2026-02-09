#!/usr/bin/env python3
"""HTTP server wrapper for Beyondworks AI Assistant.

Exposes assistant.py functionality as an HTTP API for Docker-based deployment.
Uses only Python stdlib (http.server) — no external frameworks needed.

Endpoints:
    POST /invoke  — Run assistant with JSON body
    GET  /health  — Health check

Request body for /invoke:
    {
        "domain": "router",
        "message": "내일 회의 추가해줘",
        "mode": "chat",
        "user_id": "U12345",
        "channel_id": "C12345",
        "images": [],
        "session_ttl": 30,
        "session_scope": "default"
    }
"""
import json
import os
import sys
import base64
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.session import (
    get_session,
    update_session,
    set_pending_action,
    get_and_clear_pending_action,
)
from assistant import get_handler, handle_resolve_action


def invoke_assistant(params):
    """Core logic extracted from assistant.py main() for HTTP invocation.

    Args:
        params: dict with domain, message, mode, user_id, channel_id, etc.

    Returns:
        dict with response, domain, and optional fields.
    """
    domain = params.get("domain", "router")
    message = params.get("message", "")
    mode = params.get("mode", "chat")
    user_id = params.get("user_id", "default")
    channel_id = params.get("channel_id", "default")
    image_urls = params.get("images", [])
    session_ttl = params.get("session_ttl", 30)
    session_scope = params.get("session_scope", "default")

    # Handle base64 encoded messages
    if message.startswith("b64:"):
        try:
            message = base64.b64decode(message[4:]).decode("utf-8")
        except Exception:
            pass

    # resolve_action handling
    if domain == "resolve_action":
        return handle_resolve_action(
            message, user_id, channel_id,
            session_ttl=session_ttl, session_scope=session_scope,
        )

    # Router: classify domain
    if domain == "router":
        if not message:
            return {"error": "router 모드에는 메시지가 필요합니다"}

        channel_lower = channel_id.lower() if channel_id else ""
        is_schedule_channel = "schedule" in channel_lower

        if is_schedule_channel:
            domain = "schedule"
        else:
            session = get_session(
                user_id, channel_id,
                ttl_minutes=session_ttl, session_scope=session_scope,
            )
            if session.get("pending_action"):
                domain = session.get("domain")
            else:
                from core.openai_client import classify_domain
                from core.config import get_domain_keywords_map
                domain = classify_domain(message, get_domain_keywords_map())

    # Load session
    session = None
    if mode == "chat" and user_id != "default":
        session = get_session(
            user_id, channel_id,
            ttl_minutes=session_ttl, session_scope=session_scope,
        )

    # Execute domain handler
    handler = get_handler(domain)
    if not handler:
        return {"error": f"Unknown domain: {domain}"}

    result = handler(message, mode, session, image_urls=image_urls or None)
    if not isinstance(result, dict):
        result = {"response": str(result), "domain": domain}

    # Save pending action
    if result.get("interactive"):
        pending = result.get("interactive", {}).get("pending_action")
        if pending and user_id != "default":
            set_pending_action(
                user_id, channel_id, pending,
                ttl_minutes=session_ttl, session_scope=session_scope,
            )

    # Update session
    if session is not None and mode == "chat" and message:
        resp_text = result.get("response", "")
        update_session(
            user_id, channel_id, domain, message, resp_text,
            ttl_minutes=session_ttl, session_scope=session_scope,
        )

    # Annotate learning events
    learning_events = result.get("learning_events")
    if isinstance(learning_events, list):
        for event in learning_events:
            if isinstance(event, dict):
                event.setdefault("source_message", message)
                event.setdefault("user", user_id)
                event.setdefault("channel", channel_id)

    return result


class AssistantHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the assistant API."""

    def do_POST(self):
        if self.path == "/invoke":
            self._handle_invoke()
        else:
            self._send_json(404, {"error": "Not found"})

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"error": "Not found"})

    def _handle_invoke(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            params = json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, ValueError) as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        try:
            result = invoke_assistant(params)
            self._send_json(200, result)
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {"error": str(e)})

    def _send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        """Suppress default request logging to stderr."""
        pass


def main():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), AssistantHandler)
    print(f"[assistant-server] Listening on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[assistant-server] Shutting down")
        server.server_close()


if __name__ == "__main__":
    main()
