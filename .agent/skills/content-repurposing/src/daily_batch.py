#!/usr/bin/env python3
"""
Daily Batch Script for Content Repurposing Skill
Iterates through configured categories, searches YouTube for trending videos,
and triggers the repurposing pipeline for each.
"""

import json
import os
import requests
import datetime
import time
import sys
# Ensure src is in path to find repurpose
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from repurpose import run_pipeline

def search_youtube(query, api_key, max_results=3):
    """
    Search YouTube for recent popular videos.
    """
    # Last 24 hours
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    published_after = yesterday.isoformat() + "Z"

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "key": api_key,
        "maxResults": max_results,
        "order": "viewCount",
        "publishedAfter": published_after,
        "type": "video"
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        videos = []
        for item in data.get("items", []):
            if "id" in item and "videoId" in item["id"]:
                video_id = item["id"]["videoId"]
                videos.append(f"https://www.youtube.com/watch?v={video_id}")

        return videos

    except Exception as e:
        print(f"⚠️ Error searching YouTube for '{query}': {e}")
        return []

def main():
    print("🚀 Starting Daily Batch Analysis...")

    # Check for config in CWD or Parent
    config_path = "notion_config.json"
    if not os.path.exists(config_path):
        # Check parent directory (if run from src)
        possible_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notion_config.json")
        if os.path.exists(possible_path):
            config_path = possible_path

    if not os.path.exists(config_path):
        print(f"❌ Config file not found. Checked: notion_config.json and {config_path}")
        sys.exit(1)

    print(f"📄 Loading config from: {config_path}")
    with open(config_path) as f:
        config = json.load(f)

    api_key = config.get("youtube_api_key")
    # Categories are keys in database_map or categories
    categories_map = config.get("database_map") or config.get("categories", {})

    if not api_key:
        print("❌ YouTube API Key missing in config")
        sys.exit(1)

    if not categories_map:
        print("❌ No categories configured")
        sys.exit(1)

    print(f"📂 Found {len(categories_map)} categories: {list(categories_map.keys())}")

    total_processed = 0

    for category in categories_map.keys():
        print(f"\nExample Query: '{category}'")

        # Search
        videos = search_youtube(category, api_key, max_results=3)
        print(f"🔍 Found {len(videos)} videos for '{category}'")

        for video_url in videos:
            print(f"  ▶️ Processing: {video_url}")
            try:
                # Call existing pipeline
                # NOTE: run_pipeline assumes CWD has config.
                # If config_path is not in CWD, run_pipeline might fail if it just does open("notion_config.json")
                # But we are assuming n8n sets CWD correctly.

                result = run_pipeline(video_url)
                if result:
                    total_processed += 1

                # Rate limit safety
                time.sleep(15)

            except Exception as e:
                print(f"  ❌ Failed to process {video_url}: {e}")
                import traceback
                traceback.print_exc()

        # Wait between categories
        time.sleep(5)

    print(f"\n✅ Daily Batch Completed! Total videos processed: {total_processed}")

if __name__ == "__main__":
    main()
