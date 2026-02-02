import sys
import os
from openai import OpenAI

def generate_blog_post(file_path="transcript.txt"):
    # Check for API Key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is missing.")
        sys.exit(1)

    # Read Transcript
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            transcript = f.read()
    except FileNotFoundError:
        print(f"Error: Transcript file '{file_path}' not found. Please run fetch_transcript.py first.")
        sys.exit(1)

    print("Generating blog post using GPT-4o...")

    client = OpenAI(api_key=api_key)

    system_prompt = """
    당신은 SEO 전문 블로그 작가입니다.
    제공된 유튜브 자막 스크립트를 바탕으로 전문적이고 가독성 높은 한국어 블로그 포스트를 작성해야 합니다.

    다음 가이드를 반드시 따르세요:
    1. **제목**: 클릭을 유도하는 매력적인 메인 제목과 H1 태그를 사용하세요.
    2. **요약**: 글 시작 부분에 3줄 내외의 핵심 요약을 포함하세요.
    3. **구조**: H2, H3 태그를 사용하여 논리적으로 내용을 구성하세요.
    4. **스타일**: SEO에 최적화된 키워드를 자연스럽게 포함하고, 독자에게 말을 거는 듯한 친근하지만 전문적인 어조를 사용하세요.
    5. **포맷**: 마크다운 형식을 사용하여 볼드체, 리스트, 인용구 등을 적절히 활용하세요.
    6. **결론**: 글의 마무리에 독자가 행동할 수 있는 'Call to Action'이나 결론을 포함하세요.
    """

    user_prompt = f"""
    다음은 유튜브 동영상의 자막 스크립트입니다:

    ---
    {transcript[:15000]}
    ---
    (스크립트가 너무 길 경우 앞부분 중요 내용 위주로 참고하세요)

    위 내용을 바탕으로 완벽한 SEO 블로그 포스트를 작성해 주세요.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        blog_content = response.choices[0].message.content

        output_file = "blog_post.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(blog_content)

        print(f"Success! Blog post saved to: {os.path.abspath(output_file)}")

    except Exception as e:
        print(f"Error generating blog post: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    transcript_file = sys.argv[1] if len(sys.argv) > 1 else "transcript.txt"
    generate_blog_post(transcript_file)
