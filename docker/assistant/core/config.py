"""Configuration loader for Beyondworks Assistant.

Handles environment variable loading from .env files and JSON config
parsing for multi-domain Notion workspace management. Uses only the
Python standard library.
"""

import os
import json


# Project root is one level above core/
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_env():
    """Load environment variables from .env file in the project root.

    Parses KEY=VALUE pairs, ignoring comments and blank lines.
    Uses os.environ.setdefault so existing environment variables
    are never overwritten.
    """
    env_path = os.path.join(SCRIPT_DIR, '.env')
    if not os.path.exists(env_path):
        return

    with open(env_path, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())


def load_config():
    """Load and return the parsed config.json from the project root.

    Raises FileNotFoundError if config.json does not exist.
    Raises json.JSONDecodeError if the file contains invalid JSON.
    """
    config_path = os.path.join(SCRIPT_DIR, 'config.json')
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_domain_config(domain_name):
    """Get configuration for a specific domain.

    Args:
        domain_name: Key in config.json "domains" mapping
                     (e.g. "schedule", "content", "finance").

    Returns:
        dict with domain configuration, or empty dict if not found.
    """
    config = load_config()
    return config.get('domains', {}).get(domain_name, {})


def get_all_domain_names():
    """Return a list of all configured domain names."""
    config = load_config()
    return list(config.get('domains', {}).keys())


def get_domain_keywords_map():
    """Build a mapping of domain_name -> keywords list.

    Returns:
        dict like {"schedule": ["keyword1", ...], "content": [...]}
    """
    config = load_config()
    domains = config.get('domains', {})
    return {
        name: domain.get('keywords', [])
        for name, domain in domains.items()
    }


def resolve_db_alias(alias):
    """Resolve a user-facing alias to (domain, db_key, db_id).

    Searches all domains' "aliases" mappings in config.json.
    Returns (domain_name, db_key, database_id) or (None, None, None).
    """
    config = load_config()
    domains = config.get('domains', {})
    alias_lower = alias.strip().lower().replace(" ", "")
    for domain_name, domain_cfg in domains.items():
        aliases = domain_cfg.get('aliases', {})
        for alias_name, db_key in aliases.items():
            if alias_lower == alias_name.lower().replace(" ", ""):
                db_id = domain_cfg.get('databases', {}).get(db_key, "")
                return (domain_name, db_key, db_id)
    return (None, None, None)


def get_all_aliases_map():
    """Build a flat map: alias_name -> {domain, db_key, db_id}.

    Used by workspace.py to build the DB catalog for the system prompt.
    """
    config = load_config()
    domains = config.get('domains', {})
    result = {}
    for domain_name, domain_cfg in domains.items():
        aliases = domain_cfg.get('aliases', {})
        dbs = domain_cfg.get('databases', {})
        for alias_name, db_key in aliases.items():
            db_id = dbs.get(db_key, "")
            if db_id:
                result[alias_name] = {
                    "domain": domain_name,
                    "db_key": db_key,
                    "db_id": db_id,
                }
    return result


def get_notion_key():
    """Return the Notion API key from environment."""
    return os.environ.get('NOTION_API_KEY', '')


def get_openai_key():
    """Return the OpenAI API key from environment."""
    return os.environ.get('OPENAI_API_KEY', '')


def get_ai_config():
    """Return AI provider configuration from environment.

    Reads:
        AI_PROVIDER: 'openai' or 'gemini' (default: 'openai')
        AI_MODEL: model ID (default: 'gpt-4o-mini')
        GEMINI_API_KEY: Google Gemini API key
        AI_FALLBACK_PROVIDER: optional fallback provider
        AI_FALLBACK_MODEL: optional fallback model
    """
    return {
        "provider": os.environ.get('AI_PROVIDER', 'openai'),
        "model": os.environ.get('AI_MODEL', 'gpt-4o-mini'),
        "gemini_api_key": os.environ.get('GEMINI_API_KEY', ''),
        "fallback_provider": os.environ.get('AI_FALLBACK_PROVIDER', ''),
        "fallback_model": os.environ.get('AI_FALLBACK_MODEL', 'gpt-4o-mini'),
    }


# Auto-load .env on import so keys are available immediately
load_env()
