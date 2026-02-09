"""Notion API client for Beyondworks Assistant.

Provides low-level HTTP helpers and higher-level database/page operations
for interacting with the Notion API. Uses only urllib from the standard
library -- no external dependencies.
"""

import json
import urllib.request
import urllib.error

from .config import get_notion_key
from .ssl_context import get_ssl_context

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BASE_URL = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"
_DEFAULT_TIMEOUT = 30  # seconds


# ---------------------------------------------------------------------------
# Low-level HTTP helper
# ---------------------------------------------------------------------------

def notion_request(method, endpoint, data=None):
    """Execute an authenticated request against the Notion API.

    Args:
        method:   HTTP method (GET, POST, PATCH, DELETE).
        endpoint: API path appended to the base URL, e.g. "databases/{id}/query".
        data:     Optional dict to send as JSON body.

    Returns:
        dict with keys:
            success (bool): True if the request succeeded (2xx).
            data (dict):    Parsed JSON response on success.
            error (str):    Error description on failure.
            status (int):   HTTP status code on failure (when available).
    """
    api_key = get_notion_key()
    if not api_key:
        return {"success": False, "error": "NOTION_API_KEY is not configured"}

    url = f"{_BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
    }

    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT, context=get_ssl_context()) as response:
            return {"success": True, "data": json.load(response)}
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode('utf-8') if exc.fp else str(exc)
        return {"success": False, "error": error_body, "status": exc.code}
    except urllib.error.URLError as exc:
        return {"success": False, "error": f"Network error: {exc.reason}"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---------------------------------------------------------------------------
# Rich-text helpers
# ---------------------------------------------------------------------------

def parse_rich_text(rich_text_arr):
    """Extract plain text from a Notion rich_text array.

    Args:
        rich_text_arr: List of Notion rich_text objects, each containing
                       a 'plain_text' key.

    Returns:
        Concatenated plain text string, or empty string if input is falsy.
    """
    if not rich_text_arr:
        return ""
    return "".join(item.get('plain_text', '') for item in rich_text_arr)


# ---------------------------------------------------------------------------
# Property value extractor
# ---------------------------------------------------------------------------

def _extract_property_value(prop_type, prop_value):
    """Extract a Python value from a single Notion property object.

    Args:
        prop_type:  The Notion property type string.
        prop_value: The full property dict from the API.

    Returns:
        Extracted value appropriate for the property type.
    """
    if prop_type == 'title':
        return parse_rich_text(prop_value.get('title', []))

    if prop_type == 'rich_text':
        return parse_rich_text(prop_value.get('rich_text', []))

    if prop_type == 'number':
        return prop_value.get('number')

    if prop_type == 'select':
        select_obj = prop_value.get('select')
        return select_obj.get('name', '') if select_obj else ''

    if prop_type == 'multi_select':
        items = prop_value.get('multi_select', [])
        return [item.get('name', '') for item in items]

    if prop_type == 'date':
        date_obj = prop_value.get('date')
        if not date_obj:
            return {'start': '', 'end': ''}
        return {
            'start': date_obj.get('start', ''),
            'end': date_obj.get('end', ''),
        }

    if prop_type == 'checkbox':
        return prop_value.get('checkbox', False)

    if prop_type == 'url':
        return prop_value.get('url', '')

    if prop_type == 'email':
        return prop_value.get('email', '')

    if prop_type == 'phone_number':
        return prop_value.get('phone_number', '')

    if prop_type == 'relation':
        relations = prop_value.get('relation', [])
        return [rel.get('id', '') for rel in relations]

    if prop_type == 'formula':
        formula_obj = prop_value.get('formula', {})
        formula_type = formula_obj.get('type', '')
        return formula_obj.get(formula_type)

    if prop_type == 'rollup':
        rollup_obj = prop_value.get('rollup', {})
        rollup_type = rollup_obj.get('type', '')
        if rollup_type == 'array':
            arr = rollup_obj.get('array', [])
            parsed = []
            for item in arr:
                item_type = item.get('type', '')
                if item_type:
                    parsed.append(_extract_property_value(item_type, item))
                else:
                    parsed.append(item)
            return parsed
        return rollup_obj.get(rollup_type)

    if prop_type == 'status':
        status_obj = prop_value.get('status')
        return status_obj.get('name', '') if status_obj else ''

    if prop_type == 'people':
        people = prop_value.get('people', [])
        return [
            person.get('name', person.get('id', ''))
            for person in people
        ]

    if prop_type == 'files':
        files = prop_value.get('files', [])
        extracted = []
        for file_obj in files:
            file_data = file_obj.get('file') or file_obj.get('external')
            if file_data:
                extracted.append({
                    'name': file_obj.get('name', ''),
                    'url': file_data.get('url', ''),
                })
        return extracted

    if prop_type == 'created_time':
        return prop_value.get('created_time', '')

    if prop_type == 'last_edited_time':
        return prop_value.get('last_edited_time', '')

    if prop_type == 'created_by':
        return prop_value.get('created_by', {}).get('id', '')

    if prop_type == 'last_edited_by':
        return prop_value.get('last_edited_by', {}).get('id', '')

    if prop_type == 'unique_id':
        uid = prop_value.get('unique_id', {})
        prefix = uid.get('prefix', '')
        number = uid.get('number', '')
        return f"{prefix}-{number}" if prefix else str(number)

    # Fallback for unknown property types
    return prop_value.get(prop_type)


# ---------------------------------------------------------------------------
# Relation resolution
# ---------------------------------------------------------------------------

_page_title_cache = {}


def resolve_page_title(page_id):
    """Fetch a page by ID and extract its title property.

    Uses an in-memory cache to avoid duplicate API calls within the
    same CLI invocation.

    Args:
        page_id: Notion page ID string.

    Returns:
        Title text, or the page_id itself as fallback.
    """
    if page_id in _page_title_cache:
        return _page_title_cache[page_id]

    result = notion_request("GET", f"pages/{page_id}")
    if not result["success"]:
        _page_title_cache[page_id] = page_id
        return page_id

    page = result["data"]
    props = page.get("properties", {})
    for prop_name, prop_value in props.items():
        if prop_value.get("type") == "title":
            title = parse_rich_text(prop_value.get("title", []))
            _page_title_cache[page_id] = title or page_id
            return _page_title_cache[page_id]

    _page_title_cache[page_id] = page_id
    return page_id


def resolve_relations(relation_ids):
    """Resolve a list of relation page IDs to {id, title} dicts.

    Args:
        relation_ids: List of Notion page ID strings.

    Returns:
        List of dicts with 'id' and 'title' keys.
    """
    return [
        {"id": pid, "title": resolve_page_title(pid)}
        for pid in relation_ids
        if pid
    ]


# ---------------------------------------------------------------------------
# Generic property parser (placed after resolve_relations to satisfy linter)
# ---------------------------------------------------------------------------

def parse_page_properties(page, resolve_rels=False):
    """Parse all properties of a Notion page into a flat dictionary.

    Handles the following Notion property types:
        title, rich_text, number, select, multi_select, date, checkbox,
        url, email, phone_number, relation, formula, rollup, status,
        people, files, created_time, last_edited_time, created_by,
        last_edited_by, unique_id.

    Args:
        page: A Notion page object (dict) as returned by the API.
        resolve_rels: If True, resolve relation page IDs to
            {id, title} dicts via the Notion API.

    Returns:
        dict mapping property names to their extracted Python values.
        Also includes 'id' and 'url' from the page-level metadata.
    """
    result = {
        'id': page.get('id', ''),
        'url': page.get('url', ''),
    }

    props = page.get('properties', {})

    for prop_name, prop_value in props.items():
        prop_type = prop_value.get('type', '')
        value = _extract_property_value(prop_type, prop_value)

        if resolve_rels and prop_type == 'relation' and isinstance(value, list):
            value = resolve_relations(value)

        result[prop_name] = value

    return result


# ---------------------------------------------------------------------------
# Workspace helpers
# ---------------------------------------------------------------------------

def search_workspace(query, object_type="page_or_database", page_size=20, start_cursor=None):
    """Search across the connected Notion workspace.

    Args:
        query: Search text.
        object_type: page|database|page_or_database
        page_size: max items in a single page (max 100).
        start_cursor: optional cursor for pagination.

    Returns:
        dict with success/results/next_cursor/has_more fields.
    """
    body = {
        "query": query or "",
        "page_size": min(max(page_size, 1), 100),
    }
    if object_type in {"page", "database"}:
        body["filter"] = {"property": "object", "value": object_type}
    if start_cursor:
        body["start_cursor"] = start_cursor

    response = notion_request("POST", "search", body)
    if not response["success"]:
        return {
            "success": False,
            "results": [],
            "error": response.get("error", "Unknown error"),
        }

    data = response["data"]
    return {
        "success": True,
        "results": data.get("results", []),
        "next_cursor": data.get("next_cursor"),
        "has_more": data.get("has_more", False),
    }


def get_database_schema(database_id):
    """Get full schema metadata for a Notion database."""
    response = notion_request("GET", f"databases/{database_id}")
    if not response["success"]:
        return {
            "success": False,
            "schema": {},
            "error": response.get("error", "Unknown error"),
        }

    data = response["data"]
    return {
        "success": True,
        "schema": data.get("properties", {}),
        "title": parse_rich_text(data.get("title", [])),
        "raw": data,
    }


def retrieve_page(page_id):
    """Retrieve a page object by ID."""
    response = notion_request("GET", f"pages/{page_id}")
    if not response["success"]:
        return {
            "success": False,
            "page": None,
            "error": response.get("error", "Unknown error"),
        }
    return {"success": True, "page": response["data"]}


def _normalize_key(text):
    # Remove control characters (e.g. \x08 in "\x08Date") before normalizing
    cleaned = "".join(ch for ch in (text or "") if ch.isprintable())
    return cleaned.strip().lower().replace(" ", "").replace("_", "")


def get_title_property_name(schema):
    """Return the title property name in a database schema."""
    for prop_name, prop_def in schema.items():
        if prop_def.get("type") == "title":
            return prop_name
    return None


def _coerce_property_value_for_write(prop_type, value):
    """Convert Python primitive to Notion property payload."""
    if prop_type == "title":
        return {"title": [{"text": {"content": str(value)}}]}
    if prop_type == "rich_text":
        return {"rich_text": [{"text": {"content": str(value)}}]}
    if prop_type == "number":
        try:
            return {"number": float(value)}
        except (TypeError, ValueError):
            return {"number": None}
    if prop_type == "select":
        return {"select": {"name": str(value)}} if value else {"select": None}
    if prop_type == "multi_select":
        if isinstance(value, list):
            return {"multi_select": [{"name": str(v)} for v in value if str(v).strip()]}
        if value:
            return {"multi_select": [{"name": str(value)}]}
        return {"multi_select": []}
    if prop_type == "status":
        return {"status": {"name": str(value)}} if value else {"status": None}
    if prop_type == "checkbox":
        return {"checkbox": bool(value)}
    if prop_type == "url":
        return {"url": str(value) if value else None}
    if prop_type == "email":
        return {"email": str(value) if value else None}
    if prop_type == "phone_number":
        return {"phone_number": str(value) if value else None}
    if prop_type == "date":
        if isinstance(value, dict):
            start = value.get("start")
            end = value.get("end")
            # Ensure KST timezone on datetime strings without timezone
            if start and "T" in str(start) and "+" not in str(start).split("T")[1] and "Z" not in str(start):
                start = f"{start}+09:00"
            return {"date": {"start": start, "end": end} if start else None}
        val_str = str(value) if value else ""
        # Ensure KST timezone on datetime strings without timezone
        if val_str and "T" in val_str and "+" not in val_str.split("T")[1] and "Z" not in val_str:
            val_str = f"{val_str}+09:00"
        return {"date": {"start": val_str} if val_str else None}
    if prop_type == "relation":
        if isinstance(value, list):
            return {"relation": [{"id": str(v)} for v in value if str(v).strip()]}
        if value:
            return {"relation": [{"id": str(value)}]}
        return {"relation": []}
    return None


def build_properties_from_values(schema, values):
    """Map generic key/value pairs to a database's property schema.

    The mapper tries exact and normalized name matching.
    """
    if not isinstance(values, dict):
        return {}

    normalized_schema = {_normalize_key(name): name for name in schema.keys()}
    properties = {}
    for key, value in values.items():
        if value is None:
            continue
        prop_name = None
        if key in schema:
            prop_name = key
        else:
            prop_name = normalized_schema.get(_normalize_key(str(key)))
        if not prop_name:
            continue

        prop_type = schema.get(prop_name, {}).get("type")
        if not prop_type:
            continue
        payload = _coerce_property_value_for_write(prop_type, value)
        if payload is not None:
            properties[prop_name] = payload
    return properties


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def query_database(db_id, filter_obj=None, sorts=None, page_size=100, start_cursor=None, max_results=None):
    """Query a Notion database with optional filter and sort.

    Handles pagination automatically: if there are more results than a
    single page, subsequent requests are made until all results are
    collected or an error occurs.

    Args:
        db_id:       Notion database ID.
        filter_obj:  Optional Notion filter object (dict).
        sorts:       Optional list of sort objects.
        page_size:   Number of results per page (max 100).
        start_cursor: Optional cursor for pagination resume.
        max_results: Optional upper bound for total records.

    Returns:
        dict with keys:
            success (bool): True if all pages were fetched without error.
            results (list): List of page objects.
            error (str):    Error message on failure.
    """
    all_results = []
    next_cursor = start_cursor

    while True:
        body = {"page_size": min(page_size, 100)}
        if filter_obj:
            body["filter"] = filter_obj
        if sorts:
            body["sorts"] = sorts
        if next_cursor:
            body["start_cursor"] = next_cursor

        response = notion_request("POST", f"databases/{db_id}/query", body)

        if not response["success"]:
            return {
                "success": False,
                "results": all_results,
                "error": response.get("error", "Unknown error"),
            }

        data = response["data"]
        page_results = data.get("results", [])
        all_results.extend(page_results)

        if max_results is not None and len(all_results) >= max_results:
            all_results = all_results[:max_results]
            return {
                "success": True,
                "results": all_results,
                "has_more": True,
                "next_cursor": data.get("next_cursor"),
            }

        if not data.get("has_more", False):
            break

        next_cursor = data.get("next_cursor")
        if not next_cursor:
            break

    return {
        "success": True,
        "results": all_results,
        "has_more": False,
        "next_cursor": None,
    }


# ---------------------------------------------------------------------------
# Page operations
# ---------------------------------------------------------------------------

def create_page(db_id, properties):
    """Create a new page in a Notion database.

    Args:
        db_id:      Parent database ID.
        properties: Dict of Notion property objects matching the
                    database schema.

    Returns:
        dict from notion_request with success/data/error keys.
    """
    page_data = {
        "parent": {"database_id": db_id},
        "properties": properties,
    }
    return notion_request("POST", "pages", page_data)


def update_page(page_id, properties):
    """Update properties on an existing Notion page.

    Args:
        page_id:    The page ID to update.
        properties: Dict of Notion property objects to set.

    Returns:
        dict from notion_request with success/data/error keys.
    """
    return notion_request("PATCH", f"pages/{page_id}", {"properties": properties})


def append_blocks(page_id, blocks):
    """Append children blocks to a Notion page body.

    Args:
        page_id: The page ID to append blocks to.
        blocks: List of Notion block objects.

    Returns:
        dict from notion_request with success/data/error keys.
    """
    return notion_request("PATCH", f"blocks/{page_id}/children", {"children": blocks})


def archive_page(page_id):
    """Archive (soft-delete) a Notion page.

    Args:
        page_id: The page ID to archive.

    Returns:
        dict from notion_request with success/data/error keys.
    """
    return notion_request("PATCH", f"pages/{page_id}", {"archived": True})
