import yt_dlp

def fetch_metadata(video_url):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(video_url, download=False)
            return {
                "title": info.get("title"),
                "channel": info.get("uploader"),
                "upload_date": info.get("upload_date"),
                "thumbnail": info.get("thumbnail"),
                "url": video_url,
                "description": info.get("description")
            }
        except Exception as e:
            print(f"Error fetching metadata: {e}")
            return None

if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) > 1:
        data = fetch_metadata(sys.argv[1])
        if data:
            print(json.dumps(data, indent=2))
