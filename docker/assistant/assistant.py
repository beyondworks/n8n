#!/usr/bin/env python3
"""
Beyondworks AI Assistant — Unified Router with Session Support
Usage:
  python3 assistant.py <domain> "<message>" [mode] [user_id] [channel_id]
      [--images '<json_array>'] [--session-ttl 1440] [--session-scope universal_v2]
  domain: schedule|content|finance|travel|tools|business|workspace|router|resolve_action
  mode: chat|daily_briefing|weekly_briefing|reminder|weekly_digest|monthly_report|weekly_expense|dday_reminder|payment_reminder
"""
import sys
import os
import json
import base64
import time

# Add debugging log
DEBUG_LOG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_execution.log")
try:
    with open(DEBUG_LOG_PATH, "a") as f:
        f.write(f"\n--- Execution at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        f.write(f"Args: {sys.argv}\n")
        f.write(f"CWD: {os.getcwd()}\n")
except Exception:
    pass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.session import (
    get_session,
    update_session,
    set_pending_action,
    get_and_clear_pending_action,
)


def get_handler(domain):
    if domain == "schedule":
        from domains.schedule import handle
    elif domain == "content":
        from domains.content import handle
    elif domain == "finance":
        from domains.finance import handle
    elif domain == "travel":
        from domains.travel import handle
    elif domain == "tools":
        from domains.tools import handle
    elif domain == "business":
        from domains.business import handle
    elif domain == "workspace":
        from domains.workspace import handle
    else:
        return None
    return handle


def _get_domain_exec_tool(domain):
    """Get the _exec_tool function for a domain (used by resolve_action)."""
    if domain == "finance":
        from domains.finance import _exec_tool
    elif domain == "schedule":
        from domains.schedule import _exec_tool
    elif domain == "content":
        from domains.content import _exec_tool
    elif domain == "travel":
        from domains.travel import _exec_tool
    elif domain == "tools":
        from domains.tools import _exec_tool
    elif domain == "business":
        from domains.business import _exec_tool
    elif domain == "workspace":
        from domains.workspace import _exec_tool
    else:
        return None
    return _exec_tool


def handle_resolve_action(value, user_id, channel_id, session_ttl=30, session_scope="default"):
    """Handle a button click from Slack interactive message."""
    action = get_and_clear_pending_action(
        user_id,
        channel_id,
        ttl_minutes=session_ttl,
        session_scope=session_scope,
    )
    if not action:
        return {"response": "처리할 대기 작업이 없습니다.", "domain": "unknown"}

    session = get_session(
        user_id,
        channel_id,
        ttl_minutes=session_ttl,
        session_scope=session_scope,
    )
    domain = session.get("domain", "schedule")

    tool_name = action.get("tool", "")
    if tool_name.startswith("functions."):
        tool_name = tool_name[len("functions."):]
    args = action.get("args", {})
    field_name = action.get("field_name", "")
    args[field_name] = value

    exec_tool = _get_domain_exec_tool(domain)
    if not exec_tool:
        return {"response": f"도메인 '{domain}'의 도구를 찾을 수 없습니다.", "domain": domain}

    resp = exec_tool(tool_name, args)
    update_session(
        user_id,
        channel_id,
        domain,
        f"[버튼 선택: {value}]",
        resp,
        ttl_minutes=session_ttl,
        session_scope=session_scope,
    )
    return {"response": resp, "domain": domain}


def _parse_optional_args(argv):
    """Extract optional flags and return cleaned argv and options."""
    image_urls = []
    session_ttl = 30
    session_scope = "default"
    cleaned = []
    i = 0
    while i < len(argv):
        if argv[i] == "--images" and i + 1 < len(argv):
            try:
                image_urls = json.loads(argv[i + 1])
                if not isinstance(image_urls, list):
                    image_urls = []
            except (json.JSONDecodeError, TypeError):
                image_urls = []
            i += 2
            continue
        if argv[i] == "--session-ttl" and i + 1 < len(argv):
            try:
                session_ttl = max(1, int(argv[i + 1]))
            except (TypeError, ValueError):
                session_ttl = 30
            i += 2
            continue
        if argv[i] == "--session-scope" and i + 1 < len(argv):
            session_scope = argv[i + 1] or "default"
            i += 2
            continue

        cleaned.append(argv[i])
        i += 1

    return cleaned, image_urls, session_ttl, session_scope


def main():
    argv, image_urls, session_ttl, session_scope = _parse_optional_args(sys.argv)

    if len(argv) < 2:
        print(
            json.dumps(
                {
                    "error": "Usage: assistant.py <domain> [message] [mode] [user_id] [channel_id] "
                             "[--images '<json>'] [--session-ttl <minutes>] [--session-scope <scope>]"
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    domain = argv[1]
    message = argv[2] if len(argv) > 2 else ""

    if message.startswith("b64:"):
        try:
            message = base64.b64decode(message[4:]).decode("utf-8")
        except Exception:
            pass

    mode = argv[3] if len(argv) > 3 else "chat"
    user_id = argv[4] if len(argv) > 4 else "default"
    channel_id = argv[5] if len(argv) > 5 else "default"

    if domain == "resolve_action":
        result = handle_resolve_action(
            message,
            user_id,
            channel_id,
            session_ttl=session_ttl,
            session_scope=session_scope,
        )
        print(json.dumps(result, ensure_ascii=False))
        return

    if domain == "router":
        if not message:
            print(json.dumps({"error": "router 모드에는 메시지가 필요합니다"}, ensure_ascii=False))
            sys.exit(1)

        channel_lower = channel_id.lower() if channel_id else ""
        is_schedule_channel = "schedule" in channel_lower

        if is_schedule_channel:
            domain = "schedule"
        else:
            session = get_session(
                user_id,
                channel_id,
                ttl_minutes=session_ttl,
                session_scope=session_scope,
            )

            if session.get("pending_action"):
                domain = session.get("domain")
            else:
                # AI 도메인 분류: 메시지 내용에 따라 적합한 도메인으로 라우팅
                from core.openai_client import classify_domain
                from core.config import get_domain_keywords_map
                domain = classify_domain(message, get_domain_keywords_map())

    session = None
    if mode == "chat" and user_id != "default":
        session = get_session(
            user_id,
            channel_id,
            ttl_minutes=session_ttl,
            session_scope=session_scope,
        )

    handler = get_handler(domain)
    if not handler:
        print(json.dumps({"error": f"Unknown domain: {domain}"}, ensure_ascii=False))
        sys.exit(1)

    result = handler(message, mode, session, image_urls=image_urls or None)
    if not isinstance(result, dict):
        result = {"response": str(result), "domain": domain}

    if result.get("interactive"):
        pending = result.get("interactive", {}).get("pending_action")
        if pending and user_id != "default":
            set_pending_action(
                user_id,
                channel_id,
                pending,
                ttl_minutes=session_ttl,
                session_scope=session_scope,
            )

    if session is not None and mode == "chat" and message:
        resp_text = result.get("response", "")
        update_session(
            user_id,
            channel_id,
            domain,
            message,
            resp_text,
            ttl_minutes=session_ttl,
            session_scope=session_scope,
        )

    learning_events = result.get("learning_events")
    if isinstance(learning_events, list):
        for event in learning_events:
            if isinstance(event, dict):
                event.setdefault("source_message", message)
                event.setdefault("user", user_id)
                event.setdefault("channel", channel_id)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
