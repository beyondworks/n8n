"""Domain-specific conversation history manager"""
import os
import json
from datetime import datetime
from .config import SCRIPT_DIR

DATA_DIR = os.path.join(SCRIPT_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def _path(domain):
    return os.path.join(DATA_DIR, f"history_{domain}.json")


def load_history(domain):
    p = _path(domain)
    if os.path.exists(p):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"conversations": []}


def save_history(domain, history):
    history["conversations"] = history["conversations"][-50:]
    with open(_path(domain), 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def add_to_history(domain, user_msg, assistant_msg):
    h = load_history(domain)
    h["conversations"].append({
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "assistant": assistant_msg[:200]
    })
    save_history(domain, h)


def get_recent_history(domain, n=5):
    h = load_history(domain)
    return h["conversations"][-n:]
