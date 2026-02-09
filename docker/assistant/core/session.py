"""Session management for multi-turn conversations.

Tracks conversation state per (user_id, channel_id) pair using
file-based JSON storage with TTL-based expiration.
"""

import os
import json
from datetime import datetime

from .config import SCRIPT_DIR

SESSIONS_DIR = os.path.join(SCRIPT_DIR, 'data', 'sessions')
os.makedirs(SESSIONS_DIR, exist_ok=True)

MAX_MESSAGES = 20  # Keep last 20 messages (10 turns)
DEFAULT_TTL = 30   # Minutes


def _session_path(user_id, channel_id, session_scope="default"):
    safe_scope = (session_scope or "default").replace("/", "_")
    safe_name = f"{safe_scope}_{user_id}_{channel_id}".replace("/", "_")
    return os.path.join(SESSIONS_DIR, f"{safe_name}.json")


def _empty_session(user_id, channel_id, session_scope="default"):
    now = datetime.now().isoformat()
    return {
        "user_id": user_id,
        "channel_id": channel_id,
        "session_scope": session_scope or "default",
        "domain": "",
        "messages": [],
        "pending_action": None,
        "created_at": now,
        "updated_at": now,
    }


def _is_expired(session, ttl_minutes):
    try:
        updated = datetime.fromisoformat(session.get("updated_at", ""))
        diff = (datetime.now() - updated).total_seconds() / 60
        return diff > ttl_minutes
    except (ValueError, TypeError):
        return True


def get_session(user_id, channel_id, ttl_minutes=DEFAULT_TTL, session_scope="default"):
    """Load a session, resetting if TTL expired.

    Args:
        user_id: Slack user ID.
        channel_id: Slack channel ID.
        ttl_minutes: Session timeout in minutes.

    Returns:
        Session dict with keys: user_id, channel_id, domain,
        messages, pending_action, created_at, updated_at.
    """
    path = _session_path(user_id, channel_id, session_scope)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                session = json.load(f)
            if _is_expired(session, ttl_minutes):
                session = _empty_session(user_id, channel_id, session_scope)
            else:
                session["session_scope"] = session_scope or "default"
            return session
        except (json.JSONDecodeError, KeyError):
            pass
    return _empty_session(user_id, channel_id, session_scope)


def _save_session(session):
    path = _session_path(
        session["user_id"],
        session["channel_id"],
        session.get("session_scope", "default"),
    )
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(session, f, ensure_ascii=False, indent=2)


def update_session(
    user_id,
    channel_id,
    domain,
    user_msg,
    assistant_msg,
    ttl_minutes=DEFAULT_TTL,
    session_scope="default",
):
    """Append a conversation turn to the session.

    Args:
        user_id: Slack user ID.
        channel_id: Slack channel ID.
        domain: Current domain.
        user_msg: User's message text.
        assistant_msg: Assistant's response text.
    """
    session = get_session(user_id, channel_id, ttl_minutes=ttl_minutes, session_scope=session_scope)
    session["domain"] = domain
    session["session_scope"] = session_scope or "default"
    session["messages"].append({"role": "user", "content": user_msg})
    session["messages"].append({"role": "assistant", "content": assistant_msg[:500]})
    session["messages"] = session["messages"][-MAX_MESSAGES:]
    session["updated_at"] = datetime.now().isoformat()
    _save_session(session)


def set_pending_action(user_id, channel_id, action, ttl_minutes=DEFAULT_TTL, session_scope="default"):
    """Store a pending interactive action in the session.

    Args:
        user_id: Slack user ID.
        channel_id: Slack channel ID.
        action: dict with tool, args, field_name, etc.
    """
    session = get_session(user_id, channel_id, ttl_minutes=ttl_minutes, session_scope=session_scope)
    session["session_scope"] = session_scope or "default"
    session["pending_action"] = action
    session["updated_at"] = datetime.now().isoformat()
    _save_session(session)


def get_and_clear_pending_action(user_id, channel_id, ttl_minutes=DEFAULT_TTL, session_scope="default"):
    """Retrieve and remove the pending action from the session.

    Returns:
        The pending_action dict, or None if none exists.
    """
    session = get_session(user_id, channel_id, ttl_minutes=ttl_minutes, session_scope=session_scope)
    session["session_scope"] = session_scope or "default"
    action = session.get("pending_action")
    if action:
        session["pending_action"] = None
        session["updated_at"] = datetime.now().isoformat()
        _save_session(session)
    return action


def clear_session(user_id, channel_id, session_scope="default"):
    """Reset a session entirely."""
    session = _empty_session(user_id, channel_id, session_scope)
    _save_session(session)
