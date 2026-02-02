import sys
import os
import json
import requests
import datetime
import re
import base64
from notion_client import Client

def get_db_schema(db_id, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    try:
        url = f"https://api.notion.com/v1/databases/{db_id}"
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("properties", {})
    except Exception as e:
        print(f"⚠️ Warning: Could not retrieve DB schema: {e}")
    return {}

def generate_image_nano_banana(prompt, config):
    """
    Image generation disabled - Imagen API not accessible.
    Returns None to skip image embedding.
    """
    print(f"⚠️ Image generation skipped (API not available)")
    return None

# Use the Nano Banana function
generate_image = generate_image_nano_banana

def parse_markdown_to_blocks(text):
    blocks = []
    lines = text.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        block_type = "paragraph"
        content = line

        if line.startswith('### '):
            block_type = "heading_3"
            content = line[4:]
        elif line.startswith('## '):
            block_type = "heading_2"
            content = line[3:]
        elif line.startswith('# '):
            block_type = "heading_1"
            content = line[2:]
        elif line.startswith('- ') or line.startswith('* '):
            block_type = "bulleted_list_item"
            content = line[2:]
        elif re.match(r'^\d+\.\s', line):
            block_type = "numbered_list_item"
            content = re.sub(r'^\d+\.\s', '', line)

        rich_text = []
        parts = re.split(r'(\*\*.*?\*\*)', content)
        for part in parts:
            if part.startswith('**') and part.endswith('**') and len(part) > 4:
                rich_text.append({
                    "type": "text",
                    "text": {"content": part[2:-2]},
                    "annotations": {"bold": True}
                })
            else:
                if part:
                    rich_text.append({
                        "type": "text",
                        "text": {"content": part}
                    })

        if not rich_text:
            continue

        if block_type == "paragraph":
            blocks.append({"object": "block", "type": block_type, block_type: {"rich_text": rich_text}})
        elif block_type in ["heading_1", "heading_2", "heading_3"]:
             blocks.append({"object": "block", "type": block_type, block_type: {"rich_text": rich_text}})
        elif block_type == "bulleted_list_item":
             blocks.append({"object": "block", "type": block_type, block_type: {"rich_text": rich_text}})
        elif block_type == "numbered_list_item":
             blocks.append({"object": "block", "type": block_type, block_type: {"rich_text": rich_text}})

    return blocks

def save_to_notion():
    if not os.path.exists("content.json"): sys.exit("Error: content.json missing.")
    with open("content.json") as f: data = json.load(f)
    meta = data.get("meta", {})
    sections = data.get("sections", [])

    if not os.path.exists("metadata.json"): sys.exit("Error: metadata.json missing.")
    with open("metadata.json") as f: file_meta = json.load(f)

    if not os.path.exists("notion_config.json"): sys.exit("Error: notion_config.json missing.")
    with open("notion_config.json") as f: config = json.load(f)

    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key: sys.exit("Error: NOTION_API_KEY not set.")
    notion = Client(auth=api_key)

    category = meta.get("category", "AI")
    db_map = config.get("database_map", {})
    target_db_id = db_map.get(category)
    if not target_db_id:
        if db_map: target_db_id = list(db_map.values())[0]
        else: sys.exit("Error: No databases found.")

    print(f"Saving to Category: {category} ({target_db_id})")

    # --- INSPECT SCHEMA ---
    schema = get_db_schema(target_db_id, api_key)

    # 1. Title Key
    title_key = "Entry name"
    for name, prop in schema.items():
        if prop["type"] == "title":
            title_key = name
            break

    # 2. Tags Type (Select vs Multi-select)
    tags_prop_type = "multi_select" # default
    if "Tags" in schema:
        tags_prop_type = schema["Tags"]["type"]

    # Use Korean timezone (KST = UTC+9)
    import pytz
    kst = pytz.timezone('Asia/Seoul')
    today_iso = datetime.datetime.now(kst).isoformat()

    properties = {
        title_key: {"title": [{"text": {"content": meta.get("title", "Untitled") or "Untitled"}}]},
    }

    # Date
    # Date (Include Time)
    if "Date" in schema:
        properties["Date"] = {"date": {"start": today_iso}}

    # Summary
    if "Summary" in schema and meta.get("summary"):
        properties["Summary"] = {"rich_text": [{"text": {"content": meta.get("summary")}}]}

    # URL
    if "URL" in schema and file_meta.get("url"):
        properties["URL"] = {"url": file_meta.get("url")}

    # Tags (Hardcoded to "유튜브")
    tags = ["유튜브"]
    if tags:
        tag_name = tags[0]
        if tags_prop_type == "select":
            properties["Tags"] = {"select": {"name": tag_name}}
        elif tags_prop_type == "multi_select":
            tag_objs = [{"name": t.replace(",", "")} for t in tags[:5]]
            properties["Tags"] = {"multi_select": tag_objs}

    # --- BODY CONTENT ---
    children = []

    # Sections (Iterate over the structured list)
    for section in sections:
        heading = section.get("heading")
        content_text = section.get("content", "")
        img_prompt = section.get("image_prompt")

        if heading:
            children.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": heading}}]
                }
            })

        # Image Gen
        if img_prompt:
            local_path = generate_image(img_prompt, config)
            if local_path:
                # Add a specialized Callout block explaining the image is local
                children.append({
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {"type": "text", "text": {"content": "🍌 Nano Banana Image Generated: ", "annotations": {"bold": True}}},
                            {"type": "text", "text": {"content": f"Saved locally at {local_path} (Notion API requires hosted URL for embedding)."}}
                        ],
                        "icon": {"emoji": "🍌"},
                        "color": "yellow_background"
                    }
                })

        # Parse Markdown Content
        parsed_blocks = parse_markdown_to_blocks(content_text)
        children.extend(parsed_blocks)

    # --- CREATE PAGE ---
    try:
        cover = None
        if file_meta.get("thumbnail"):
            cover = {"type": "external", "external": {"url": file_meta["thumbnail"]}}

        page = notion.pages.create(
            parent={"database_id": target_db_id},
            properties=properties,
            cover=cover,
            children=children
        )
        print(f"✅ Successfully saved to Notion: {page['url']}")

    except Exception as e:
        print(f"❌ Error saving to Notion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    save_to_notion()
