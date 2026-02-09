"""Persistent memory for self-learning rules.

Stores user-taught rules, corrections, and preferences in a JSON file.
Each domain has its own rule set. Rules are injected into system prompts
so the AI model adapts its behavior over time.

Storage: data/memory.json
"""

import os
import json
from datetime import datetime

from .config import SCRIPT_DIR

MEMORY_PATH = os.path.join(SCRIPT_DIR, 'data', 'memory.json')
os.makedirs(os.path.dirname(MEMORY_PATH), exist_ok=True)

MAX_RULES_PER_DOMAIN = 50


def _load_memory():
    if os.path.exists(MEMORY_PATH):
        try:
            with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"rules": {}, "corrections": [], "updated_at": ""}


def _save_memory(memory):
    memory["updated_at"] = datetime.now().isoformat()
    with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def add_rule(domain, rule_text, category="general"):
    """Add a learned rule for a domain.

    Args:
        domain: Domain name (finance, schedule, etc.) or "global".
        rule_text: The rule content as a string.
        category: Rule category (general, mapping, preference, correction).

    Returns:
        dict with success status and current rule count.
    """
    memory = _load_memory()
    if domain not in memory["rules"]:
        memory["rules"][domain] = []

    # Check for duplicate
    for existing in memory["rules"][domain]:
        if existing["text"] == rule_text:
            return {"success": False, "reason": "duplicate", "count": len(memory["rules"][domain])}

    memory["rules"][domain].append({
        "text": rule_text,
        "category": category,
        "created_at": datetime.now().isoformat(),
        "used_count": 0,
    })

    # Enforce max rules per domain (remove oldest if exceeded)
    if len(memory["rules"][domain]) > MAX_RULES_PER_DOMAIN:
        memory["rules"][domain] = memory["rules"][domain][-MAX_RULES_PER_DOMAIN:]

    _save_memory(memory)
    return {"success": True, "count": len(memory["rules"][domain])}


def remove_rule(domain, rule_index):
    """Remove a rule by index.

    Args:
        domain: Domain name.
        rule_index: 0-based index of the rule to remove.

    Returns:
        dict with success status.
    """
    memory = _load_memory()
    rules = memory.get("rules", {}).get(domain, [])
    if 0 <= rule_index < len(rules):
        removed = rules.pop(rule_index)
        _save_memory(memory)
        return {"success": True, "removed": removed["text"]}
    return {"success": False, "reason": "invalid index"}


def get_rules(domain, include_global=True):
    """Get all rules for a domain (plus global rules).

    Args:
        domain: Domain name.
        include_global: Whether to include rules from "global" domain.

    Returns:
        List of rule dicts.
    """
    memory = _load_memory()
    rules = list(memory.get("rules", {}).get(domain, []))
    if include_global and domain != "global":
        rules.extend(memory.get("rules", {}).get("global", []))
    return rules


def get_rules_as_prompt(domain):
    """Format learned rules as a system prompt section.

    Returns an empty string if no rules exist, otherwise returns
    a formatted block that can be appended to system prompts.
    """
    rules = get_rules(domain)
    if not rules:
        return ""

    lines = ["\n\n## 학습된 규칙 (사용자가 가르쳐준 내용)"]
    for i, rule in enumerate(rules):
        cat = rule.get("category", "general")
        prefix = {"mapping": "매핑", "preference": "선호", "correction": "수정", "general": "규칙"}.get(cat, "규칙")
        lines.append(f"- [{prefix}] {rule['text']}")

    # Bump usage count
    memory = _load_memory()
    for r in memory.get("rules", {}).get(domain, []):
        r["used_count"] = r.get("used_count", 0) + 1
    if domain != "global":
        for r in memory.get("rules", {}).get("global", []):
            r["used_count"] = r.get("used_count", 0) + 1
    _save_memory(memory)

    return "\n".join(lines)


def add_correction(user_msg, wrong_response, correction):
    """Record a correction for learning.

    Args:
        user_msg: Original user message.
        wrong_response: What the AI said incorrectly.
        correction: What it should have done.
    """
    memory = _load_memory()
    memory["corrections"].append({
        "user_msg": user_msg,
        "wrong": wrong_response[:200],
        "correction": correction,
        "created_at": datetime.now().isoformat(),
    })
    # Keep last 100 corrections
    memory["corrections"] = memory["corrections"][-100:]
    _save_memory(memory)


def list_rules(domain=None):
    """List all rules, optionally filtered by domain.

    Returns:
        dict mapping domain names to lists of rule texts.
    """
    memory = _load_memory()
    all_rules = memory.get("rules", {})
    if domain:
        return {domain: all_rules.get(domain, [])}
    return all_rules
