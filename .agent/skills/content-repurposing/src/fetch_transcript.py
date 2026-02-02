import sys
import os
import json
from apify_client import ApifyClient

def fetch_transcript(video_url):
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("Error: APIFY_API_TOKEN environment variable is missing.")
        sys.exit(1)

    print(f"Fetching transcript for: {video_url} using Apify...")

    try:
        client = ApifyClient(token)
        run_input = {
            "videoUrl": video_url,
            "language": "ko",
            "addTimestamp": False
        }

        # Run Actor
        run = client.actor("pintostudio/youtube-transcript-scraper").call(run_input=run_input)

        # Fetch Results
        print("Actor run finished. Fetching results...")
        dataset_items = client.dataset(run["defaultDatasetId"]).list_items().items

        if not dataset_items:
            print("Error: No transcript data returned from Apify.")
            sys.exit(1)

        item = dataset_items[0]
        transcript_text = ""

        # Handle 'data' as a list of segments (Observed structure)
        if "data" in item and isinstance(item["data"], list):
            segments = item["data"]
            texts = [seg.get("text", "") for seg in segments]
            transcript_text = " ".join(texts)

        # Fallbacks for other structures
        elif "text" in item:
            transcript_text = item["text"]
        elif "transcript" in item:
             transcript_text = item["transcript"]

        if not transcript_text:
            print(f"Error: Could not parse transcript. Item structure: {item.keys()}")
            if "data" in item:
                 print(f"Data type: {type(item['data'])}")
            sys.exit(1)

        final_output = "transcript.txt"
        with open(final_output, 'w', encoding='utf-8') as f:
            f.write(transcript_text)

        print(f"Success! Transcript saved to: {os.path.abspath(final_output)}")
        print("PREVIEW_START")
        print(transcript_text[:500] + "..." if len(transcript_text) > 500 else transcript_text)
        print("PREVIEW_END")

    except Exception as e:
        print(f"Error calling Apify: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 src/fetch_transcript.py <youtube_url>")
        sys.exit(1)

    fetch_transcript(sys.argv[1])
