---
name: content-repurposing
description: Extracts YouTube transcripts using Apify and repurposes them into blog posts.
version: 1.1.0 (Apify)
author: Antigravity
---

# Content Repurposing Skill (Apify Version)

This skill automates the process of turning YouTube videos into written content. It uses **Apify** (`pintostudio/youtube-transcript-scraper`) to reliably fetch subtitles, bypassing local IP blocking issues.

## Prerequisites
- **Apify API Token**: Get a free token from [Apify Console](https://console.apify.com/).
- Monthly Free Tier: ~1000 requests (sufficient for most users).

## Setup
1. Install dependencies:
   ```bash
   pip install --user -r requirements.txt
   ```

## Usage
Run the script with your Apify Token and a YouTube URL:
```bash
APIFY_API_TOKEN=your_token_here python3 src/fetch_transcript.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The script will save the transcript to `transcript.txt` in the current directory.

## 2. Generate Blog Post
Run the generation script with your OpenAI API Key:
```bash
OPENAI_API_KEY=sk-proj-... python3 src/blog_gen.py
```
- The script reads `transcript.txt` and uses GPT-4o to write a blog post.
- The result is saved to `blog_post.md`.

## Workflow Integration
After fetching the transcript, the Agent (Me) will:
1. Read the `transcript.txt` file.
2. Generate a structured Blog Post based on the content.
3. Save the Blog Post as a Markdown file.
