import sys
import os
import json
from openai import OpenAI

def generate_content():
    # 1. Load Config (to get categories)
    if not os.path.exists("notion_config.json"):
        print("Error: notion_config.json not found.")
        sys.exit(1)

    with open("notion_config.json") as f:
        config = json.load(f)
        categories = list(config.get("category_map", {}).keys())
        if not categories:
            categories = ['AI', 'Design', 'Branding', 'Build', 'Marketing']

    # 2. Load Transcript
    if not os.path.exists("transcript.txt"):
        print("Error: transcript.txt not found.")
        sys.exit(1)

    with open("transcript.txt", "r", encoding="utf-8") as f:
        # FIX: Correct common transcript error "M8" -> "n8n"
        transcript = f.read().replace("M8", "n8n")

    # 3. Call OpenAI
    api_key = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    system_prompt = f"""
    You are an expert content repurposer and SEO specialist.
    Your goal is to convert a YouTube transcript into a high-quality, engaging blog post optimized for search engines (Naver/Google).

    You must output a JSON object with two main keys: "meta" and "sections".

    "meta": {{
        "category": "Select one from: {json.dumps(categories)}",
        "title": "Catchy, SEO-optimized Title (Korean)",
        "summary": "2-sentence summary",
        "tags": ["Tag1", "Tag2", "Tag3", "Tag4", "Tag5"]
    }}

    "sections": [
        {{
            "type": "intro",
            "heading": "Introduction Heading",
            "content": "Introductory paragraph(s) in Markdown."
        }},
        {{
            "type": "main",
            "heading": "Section Heading",
            "content": "Main content for this section in Markdown. Use bullet points if needed.",
            "image_prompt": "A detailed prompting description for an AI image generator to visualize this section's concept. (English)"
        }},
        {{
            "type": "main",
            "heading": "Another Section",
            "content": "More content...",
            "image_prompt": "Another image prompt...(English)"
        }},
        {{
            "type": "conclusion",
            "heading": "Conclusion",
            "content": "Concluding remarks."
        }}
    ]

    Detailed Guidelines:
    - **Language**: Korean (except image prompts).
    - **Tone**: Professional yet accessible, engaging.
    - **Formatting**: Use clean Markdown (bolding key phrases, lists).
    - **Structure**: Break down valid topics into distinct 'main' sections.
    - **Image Prompts**: Generate 1-2 relevant image prompts for the main sections.
    """

    user_prompt = f"""
    Analyze this transcript and generate the required JSON structure:

    {transcript[:25000]}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )

        content_json = response.choices[0].message.content
        data = json.loads(content_json)

        # Save to file
        with open("content.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print("Content generated and classified successfully.")
        print(f"Selected Category: {data.get('meta', {}).get('category')}")

    except Exception as e:
        print(f"Error generating content: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    generate_content()
