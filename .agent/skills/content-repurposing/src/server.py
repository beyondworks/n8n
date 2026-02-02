#!/usr/bin/env python3
"""
HTTP Server wrapper for the Content Repurposing Skill.
Run this server, then call it from n8n via HTTP Request node.

Usage:
    python3 src/server.py

Endpoint:
    POST http://localhost:8765/repurpose
    Body: {"url": "https://www.youtube.com/watch?v=VIDEO_ID"}
"""

import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import subprocess
import traceback

# 서버 포트
PORT = 8765

# 스크립트 디렉토리
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

class RepurposeHandler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_OPTIONS(self):
        """CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        """Health check"""
        if self.path == "/" or self.path == "/health":
            self._send_json(200, {
                "status": "ok",
                "message": "Content Repurposing Server is running",
                "endpoint": "POST /repurpose with {\"url\": \"youtube_url\"}"
            })
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path == "/repurpose":
            try:
                # Read body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf-8'))

                url = data.get("url", "")
                if not url:
                    self._send_json(400, {"error": "Missing 'url' parameter"})
                    return

                print(f"\n{'='*50}")
                print(f"📺 Processing: {url}")
                print(f"{'='*50}")

                # Run repurpose.py
                result = subprocess.run(
                    [sys.executable, os.path.join(SCRIPT_DIR, "repurpose.py"), url],
                    capture_output=True,
                    text=True,
                    cwd=PROJECT_DIR,
                    timeout=300  # 5분 타임아웃
                )

                success = result.returncode == 0

                # Try to read content.json for response
                content_data = None
                content_path = os.path.join(PROJECT_DIR, "content.json")
                if os.path.exists(content_path):
                    try:
                        with open(content_path, 'r', encoding='utf-8') as f:
                            content_data = json.load(f)
                    except:
                        pass

                response = {
                    "success": success,
                    "url": url,
                    "stdout": result.stdout,
                    "stderr": result.stderr if not success else None,
                    "content": content_data
                }

                self._send_json(200 if success else 500, response)

            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON"})
            except subprocess.TimeoutExpired:
                self._send_json(504, {"error": "Processing timeout (5 minutes)"})
            except Exception as e:
                self._send_json(500, {
                    "error": str(e),
                    "traceback": traceback.format_exc()
                })
        else:
            self._send_json(404, {"error": "Not found. Use POST /repurpose"})

def main():
    os.chdir(PROJECT_DIR)
    server = HTTPServer(('0.0.0.0', PORT), RepurposeHandler)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║   Content Repurposing Server                             ║
╠══════════════════════════════════════════════════════════╣
║   URL: http://localhost:{PORT}                            ║
║   Endpoint: POST /repurpose                              ║
║   Body: {{"url": "https://youtube.com/watch?v=..."}}       ║
╚══════════════════════════════════════════════════════════╝
""")
    print("Server started. Press Ctrl+C to stop.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()

if __name__ == "__main__":
    main()
