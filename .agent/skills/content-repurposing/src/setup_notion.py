import os
import sys
import json
from notion_client import Client

PAGE_ID = "241003c7f7be800bb71cdf3acddc5bb8"

def setup_notion():
    print("--- Notion Integration Setup ---")

    # 1. Get API Key
    api_key = os.environ.get("NOTION_API_KEY")
    if not api_key:
        api_key = input("Enter your Notion Internal Integration Token: ").strip()
        if not api_key:
            print("Error: API Token is required.")
            sys.exit(1)

    notion = Client(auth=api_key)

    print(f"Scanning Page {PAGE_ID} for databases...")

    valid_databases = {}

    try:
        # Search for databases, but unfortunately 'search' finds everything the bot has access to.
        # Efficient way: List children of the block/page

        response = notion.blocks.children.list(block_id=PAGE_ID)

        for block in response["results"]:
            if block["type"] == "child_database":
                db_id = block["id"]
                db_title = block["child_database"]["title"]

                # Filter 'Scrap to Notion'
                if "Scrap to Notion" in db_title:
                    continue

                print(f"Found Database: {db_title}")
                valid_databases[db_title] = db_id

        if not valid_databases:
            print("No new databases found on this page. Make sure:")
            print("1. You have invited your Linkbrain/Antigravity Bot to the Notion Page.")
            print("2. The databases are directly inside the page as Child Databases (not linked views).")
            # Fallback if no children found (maybe they are linked views? handling linked views is harder)
            # If 0 found, allow manual entry?

    except Exception as e:
        print(f"Error accessing Notion: {str(e)}")
        print("Hint: Did you share the Notion Page with your Bot Integration?")
        sys.exit(1)

    # Save Config
    config = {
        "api_key": api_key,
        "databases": valid_databases
    }

    with open("notion_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\nSuccess! Configuration saved to notion_config.json")
    print(f"Found {len(valid_databases)} categories: {list(valid_databases.keys())}")

if __name__ == "__main__":
    setup_notion()
