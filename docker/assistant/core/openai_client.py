"""OpenAI API client with multi-turn tool execution (stdlib only).

Provides backward-compatible single-turn functions and a new
multi-turn tool execution loop with provider abstraction.
"""
import base64
import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from .config import get_openai_key
from .ssl_context import get_ssl_context


# ---------------------------------------------------------------------------
# Markdown stripping
# ---------------------------------------------------------------------------

def strip_markdown(text):
    """Remove markdown formatting from AI output.

    Strips bold, italic, headers, links, code blocks, and inline code
    while preserving the readable content and emoji.
    """
    if not text:
        return ""
    # Code blocks
    text = re.sub(r'```[\s\S]*?```', '', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Bold/italic (order matters: ** before *)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    # Links [text](url) → text (url)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 (\2)', text)
    # Headers
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    # Clean up extra blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Legacy single-turn functions (kept for backward compatibility)
# ---------------------------------------------------------------------------

def chat_completion(messages, model=None, max_tokens=1000, temperature=0.4):
    """Single-turn chat completion via the configured AI provider.

    Used by briefings and scheduled modes. The ``model`` parameter is
    accepted for backward-compatibility but ignored — the provider's
    model from .env is used instead.
    """
    from .ai_provider import get_provider

    provider = get_provider()
    result = provider.chat(messages, max_tokens=max_tokens, temperature=temperature)
    return result.get("content") or ""


def chat_with_tools(system_prompt, user_content, tools, model="gpt-4o-mini", max_tokens=1000):
    """Legacy single-turn tool call. Kept for scheduled modes."""
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
        "tools": tools,
        "tool_choice": "auto",
        "max_tokens": max_tokens,
        "temperature": 0.4
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode('utf-8'),
        headers={
            "Authorization": f"Bearer {get_openai_key()}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=60, context=get_ssl_context()) as resp:
            result = json.load(resp)
            msg = result['choices'][0]['message']
            tool_calls = msg.get('tool_calls', [])
            if tool_calls:
                calls = []
                for tc in tool_calls:
                    calls.append({
                        "name": tc['function']['name'],
                        "arguments": json.loads(tc['function']['arguments'])
                    })
                return msg.get('content', ''), calls
            return msg.get('content', ''), []
    except Exception as e:
        return f"AI 응답 오류: {e}", []


# ---------------------------------------------------------------------------
# Multi-turn tool execution loop (new)
# ---------------------------------------------------------------------------

# Sentinel tool names
REQUEST_USER_CHOICE = "request_user_choice"
LEARN_RULE = "learn_rule"

# Shared tool definition for all domains
REQUEST_USER_CHOICE_TOOL = {
    "type": "function",
    "function": {
        "name": REQUEST_USER_CHOICE,
        "description": "사용자에게 선택지를 제시하여 누락된 정보를 확인합니다. Slack 버튼으로 표시됩니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "사용자에게 보여줄 질문"
                },
                "options": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "선택지 목록 (최대 5개)"
                },
                "field_name": {
                    "type": "string",
                    "description": "이 선택이 채울 필드명"
                },
                "pending_tool": {
                    "type": "string",
                    "description": "선택 후 실행할 도구명"
                },
                "pending_args": {
                    "type": "object",
                    "description": "이미 수집된 인자들"
                }
            },
            "required": ["question", "options", "field_name", "pending_tool", "pending_args"]
        }
    }
}


LEARN_RULE_TOOL = {
    "type": "function",
    "function": {
        "name": LEARN_RULE,
        "description": "사용자의 피드백, 수정 요청, 선호도를 영구 규칙으로 저장합니다. "
                       "사용자가 '앞으로는 ~해줘', '~ 아니야, ~야', '~로 바꿔줘', "
                       "'~할 때는 ~해줘' 같은 말을 하면 이 도구로 학습하세요.",
        "parameters": {
            "type": "object",
            "properties": {
                "rule": {
                    "type": "string",
                    "description": "학습할 규칙 내용 (한국어, 명확하게)"
                },
                "category": {
                    "type": "string",
                    "enum": ["mapping", "preference", "correction", "general"],
                    "description": "규칙 유형: mapping(분류 매핑), preference(선호), correction(수정), general(일반)"
                }
            },
            "required": ["rule", "category"]
        }
    }
}


def _download_slack_image(url, bot_token):
    """Download a Slack private image and return a base64 data URI.

    Uses the Slack API files endpoint as a fallback when direct
    url_private access fails (requires files:read scope).

    Args:
        url: Slack url_private or url_private_download URL.
        bot_token: Slack Bot User OAuth Token (xoxb-...).

    Returns:
        base64 data URI string, or None on failure.
    """
    # Try direct download with Bearer token (works with files:read scope)
    try:
        # Prevent redirect to Slack login page
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                if "slack.com" in newurl and "/files-pri/" not in newurl:
                    raise urllib.error.HTTPError(
                        newurl, code, "redirect to login", headers, fp
                    )
                return super().redirect_request(req, fp, code, msg, headers, newurl)

        opener = urllib.request.build_opener(_NoRedirect)
        # Ensure HTTPS verification works even when Python's default CA bundle is missing.
        opener.add_handler(urllib.request.HTTPSHandler(context=get_ssl_context()))
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {bot_token}"},
        )
        with opener.open(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            # Verify we got an image, not an HTML page
            if "text/html" in content_type:
                raise ValueError("Got HTML instead of image")
            data = resp.read()
            if len(data) > 20 * 1024 * 1024:  # 20MB limit
                return None
            b64 = base64.b64encode(data).decode("ascii")
            return f"data:{content_type};base64,{b64}"
    except Exception:
        pass

    # Fallback: try extracting file_id and using Slack API
    # url_private format: files.slack.com/files-pri/TEAM-FILEID/filename
    try:
        parts = url.split("/files-pri/")
        if len(parts) > 1:
            file_id = parts[1].split("/")[0].split("-", 1)[1] if "-" in parts[1].split("/")[0] else ""
            if file_id:
                api_url = f"https://slack.com/api/files.info?file={file_id}"
                req = urllib.request.Request(
                    api_url,
                    headers={"Authorization": f"Bearer {bot_token}"},
                )
                with urllib.request.urlopen(req, timeout=10, context=get_ssl_context()) as resp:
                    info = json.load(resp)
                    if info.get("ok"):
                        dl_url = info["file"].get("url_private_download", "")
                        if dl_url:
                            req2 = urllib.request.Request(
                                dl_url,
                                headers={"Authorization": f"Bearer {bot_token}"},
                            )
                            with urllib.request.urlopen(req2, timeout=30, context=get_ssl_context()) as resp2:
                                ct = resp2.headers.get("Content-Type", "image/jpeg")
                                if "text/html" in ct:
                                    return None
                                data = resp2.read()
                                b64 = base64.b64encode(data).decode("ascii")
                                return f"data:{ct};base64,{b64}"
    except Exception:
        pass

    return None


def resolve_image_urls(image_urls):
    """Convert Slack private image URLs to base64 data URIs.

    Public URLs and existing data URIs are passed through unchanged.
    Slack private URLs (files.slack.com) are downloaded using
    SLACK_BOT_TOKEN from environment and converted to base64 data URIs.

    Args:
        image_urls: List of image URL strings.

    Returns:
        List of resolved URLs (base64 data URIs or public URLs).
    """
    if not image_urls:
        return []

    bot_token = os.environ.get("SLACK_BOT_TOKEN", "")
    resolved = []

    for url in image_urls[:5]:  # 최대 5장
        if not url:
            continue
        # Already a data URI — pass through
        if url.startswith("data:"):
            resolved.append(url)
        # Slack private URL — download with bot token
        elif "files.slack.com" in url:
            if bot_token:
                data_uri = _download_slack_image(url, bot_token)
                if data_uri:
                    resolved.append(data_uri)
            # No bot token → skip (GPT can't access private Slack URLs)
        else:
            # Public URL — pass through (GPT can fetch it directly)
            resolved.append(url)

    return resolved


def _build_multimodal_content(text, image_urls):
    """Build OpenAI multimodal content array from text and image URLs.

    Args:
        text: Text content string.
        image_urls: List of image URL strings (can be http URLs or base64 data URIs).

    Returns:
        list of content blocks for the OpenAI messages API.
    """
    content = [{"type": "text", "text": text}]
    for url in image_urls:
        content.append({
            "type": "image_url",
            "image_url": {"url": url, "detail": "auto"},
        })
    return content


def _has_action_claim_without_tool_call(response_text, recent_tool_calls):
    """
    응답에 "완료", "추가했습니다" 등의 행동 완료 표현이 있지만
    실제 도구 호출이 없는 경우를 탐지합니다 (할루시네이션 방지).

    Args:
        response_text: AI의 응답 텍스트
        recent_tool_calls: 최근 도구 호출 목록 (빈 리스트면 호출 없음)

    Returns:
        True if hallucination detected, False otherwise
    """
    if not response_text:
        return False

    # 행동 완료를 나타내는 표현들
    action_claims = [
        "완료했습니다", "추가했습니다", "생성했습니다", "만들었습니다",
        "기입했습니다", "저장했습니다", "수정했습니다", "삭제했습니다",
        "일정이 추가", "일정을 추가", "페이지를 만들", "페이지가 만들",
        "일정이 생성", "일정을 생성"
    ]

    response_lower = response_text.lower()

    # 행동 완료 표현이 있는지 확인
    has_claim = any(claim in response_lower for claim in action_claims)

    if not has_claim:
        return False

    # 도구 호출이 있었는지 확인
    if recent_tool_calls:
        return False  # 도구 호출이 있었으므로 정상

    # "이미"라는 단어가 있으면 이전 상태를 참조하는 것이므로 pass
    # (단, "이미 추가했습니다"는 여전히 할루시네이션일 수 있음 - 검색 없이 말하면)
    if "이미" in response_lower:
        # 검색/조회 도구 없이 "이미"라고 하면 할루시네이션
        return True

    return True  # 행동 완료 표현은 있지만 도구 호출이 없음


def chat_with_tools_multi(system_prompt, messages, tools, tool_executor,
                          max_tokens=1500, max_tool_rounds=3, domain="",
                          image_urls=None, force_tool_call=False):
    """Multi-turn chat with tool execution loop.

    Uses the configured AI provider (OpenAI/Gemini) from ai_provider.py.
    Executes tool calls in a loop, feeding results back to the model.

    Args:
        system_prompt: System prompt string.
        messages: List of {role, content} message dicts (conversation history).
        tools: List of tool definitions.
        tool_executor: Callable(name, args) -> str that executes a tool.
        max_tokens: Maximum response tokens per turn.
        max_tool_rounds: Maximum tool execution rounds.
        domain: Domain name for learn_rule routing.
        image_urls: Optional list of image URLs to attach to the last user message.
        force_tool_call: If True, strongly encourage tool calling for command-like requests.

    Returns:
        dict with keys:
            response (str): Final text response (markdown stripped).
            interactive (dict|None): Interactive payload if request_user_choice
                was called, containing question, options, action_id_prefix,
                and pending_action.
    """
    from .ai_provider import get_provider

    provider = get_provider()

    # 명령형 요청이면 시스템 프롬프트 강화
    if force_tool_call:
        enhanced_prompt = system_prompt + "\n\n⚠️ CRITICAL: 현재 요청은 명령형입니다. 반드시 적절한 도구를 호출해야 합니다. 도구 호출 없이 응답하면 시스템 오류가 발생합니다."
        full_messages = [{"role": "system", "content": enhanced_prompt}] + messages
    else:
        full_messages = [{"role": "system", "content": system_prompt}] + messages

    learning_events = []
    executed_tool_calls = []  # 모든 턴에서 실행된 도구 추적

    # Attach images to the last user message if provided
    if image_urls:
        # Resolve Slack private URLs → base64 data URIs
        resolved = resolve_image_urls(image_urls)
        if resolved:
            for i in range(len(full_messages) - 1, -1, -1):
                if full_messages[i].get("role") == "user":
                    text = full_messages[i].get("content", "")
                    if isinstance(text, str):
                        full_messages[i] = {
                            "role": "user",
                            "content": _build_multimodal_content(text, resolved),
                        }
                    break

    for _ in range(max_tool_rounds):
        result = provider.chat(full_messages, tools, max_tokens)
        tool_calls = result.get("tool_calls", [])

        if not tool_calls:
            # 도구 호출 없이 응답 → 할루시네이션 검사
            # 단, 이전 턴에서 도구를 실행했으면 정상 완료 응답이므로 skip
            response_text = result.get("content", "")
            if not executed_tool_calls and _has_action_claim_without_tool_call(response_text, tool_calls):
                # 할루시네이션 감지: "완료했습니다"라고 하지만 어떤 턴에서도 도구 호출이 없음
                return {
                    "response": "⚠️ 요청을 처리하려고 했지만 실행에 실패했습니다. 구체적으로 다시 요청해주세요.\n(예: '내일 오후 2시 회의 추가해줘')",
                    "interactive": None,
                    "learning_events": learning_events,
                }
            return {
                "response": strip_markdown(response_text),
                "interactive": None,
                "learning_events": learning_events,
            }

        # Handle learn_rule internally (not dispatched to domain executor)
        for tc in tool_calls:
            if tc["name"] == LEARN_RULE:
                from .memory import add_rule
                args = tc["arguments"]
                target_domain = domain or "global"
                rule_text = args.get("rule", "")
                category = args.get("category", "general")
                add_result = add_rule(target_domain, rule_text, category)
                learning_events.append({
                    "rule": rule_text,
                    "category": category,
                    "domain": target_domain,
                    "created_at": datetime.now().isoformat(),
                    "status": "learned" if add_result.get("success") else add_result.get("reason", "skipped"),
                })
                # Remove this tool call and let AI continue with remaining calls
                tool_calls = [t for t in tool_calls if t["name"] != LEARN_RULE]
                if not tool_calls:
                    # Only learn_rule was called — let AI respond with confirmation
                    confirm_msg = f"규칙을 학습했습니다: {args.get('rule', '')}"
                    return {
                        "response": strip_markdown(result.get("content", "") or confirm_msg),
                        "interactive": None,
                        "learning_events": learning_events,
                    }
                break

        # Check for interactive user choice request
        for tc in tool_calls:
            if tc["name"] == REQUEST_USER_CHOICE:
                args = tc["arguments"]
                return {
                    "response": strip_markdown(result.get("content", "") or args.get("question", "")),
                    "interactive": {
                        "question": args.get("question", ""),
                        "options": args.get("options", [])[:5],
                        "action_id_prefix": f"{args.get('pending_tool', 'action')}_{args.get('field_name', 'field')}",
                        "pending_action": {
                            "tool": args.get("pending_tool", ""),
                            "args": args.get("pending_args", {}),
                            "field_name": args.get("field_name", ""),
                        },
                    },
                    "learning_events": learning_events,
                }

        # Build assistant message with tool calls for the conversation
        assistant_msg = {
            "role": "assistant",
            "content": result.get("content"),
            "tool_calls": [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {
                        "name": tc["name"],
                        "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                    },
                }
                for tc in tool_calls
            ],
        }
        full_messages.append(assistant_msg)

        # Execute each tool and append results
        for tc in tool_calls:
            tool_result = tool_executor(tc["name"], tc["arguments"])
            executed_tool_calls.append(tc["name"])
            full_messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": str(tool_result),
            })

    # Exhausted rounds — return last content
    return {
        "response": strip_markdown(result.get("content", "처리 한도를 초과했습니다.")),
        "interactive": None,
        "learning_events": learning_events,
    }


# ---------------------------------------------------------------------------
# Domain classification (unchanged)
# ---------------------------------------------------------------------------

def classify_domain(message, domain_keywords):
    """Classify a user message into a domain.

    Uses keyword matching first (fast, reliable), then falls back to
    the configured AI provider for ambiguous messages.
    """
    msg_lower = message.lower()

    # --- Phase 1: keyword scoring (instant, no API call) ---
    # Use word-boundary-aware matching: only count keywords that appear
    # as standalone tokens, not as substrings of longer words.
    # Short keywords (<=2 chars) require exact word boundaries.
    import re as _re

    scores = {}
    for domain, keywords in domain_keywords.items():
        score = 0
        for kw in keywords:
            kw_lower = kw.lower()
            if len(kw_lower) <= 2:
                # Short keywords: require word boundary (prevent "패키지" matching "키")
                if _re.search(r'(?:^|[\s,.\'"!?()~])' + _re.escape(kw_lower) + r'(?:$|[\s,.\'"!?()~])', msg_lower):
                    score += 1
            else:
                if kw_lower in msg_lower:
                    score += 1
        if score > 0:
            scores[domain] = score

    if scores:
        best = max(scores, key=scores.get)
        top_score = scores[best]
        tied = [d for d, s in scores.items() if s == top_score]
        # Clear winner with significant margin — return immediately
        if len(tied) == 1:
            sorted_scores = sorted(scores.values(), reverse=True)
            second_best = sorted_scores[1] if len(sorted_scores) > 1 else 0
            if top_score >= second_best * 2 or top_score >= 3:
                return best
            # Narrow margin — fall through to AI for disambiguation
        # Multiple domains tied — fall through to AI

    # --- Phase 2: AI classification (for ambiguous messages) ---
    from .ai_provider import get_provider

    domains_desc = "\n".join(
        f"- {name}: {', '.join(kw)}" for name, kw in domain_keywords.items()
    )
    system_msg = (
        "You are a domain classifier. Given a user message, output ONLY "
        "one domain name from: schedule, content, finance, travel, tools, business, workspace. "
        "No explanation, no punctuation — just the domain name."
    )
    user_msg = f"""도메인 목록:
{domains_desc}

사용자 메시지: {message}

도메인:"""
    provider = get_provider()
    result = provider.chat(
        [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        max_tokens=50,
        temperature=0,
    )
    text = (result.get("content") or "").strip().lower()
    valid = {"schedule", "content", "finance", "travel", "tools", "business", "workspace"}
    for d in valid:
        if d in text:
            return d
    return "schedule"
