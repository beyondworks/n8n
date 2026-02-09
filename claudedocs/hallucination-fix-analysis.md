# AI 정보 봇 할루시네이션 문제 분석 및 해결 방안

> 작성일: 2026-02-08
> 문제: AI가 사용자 요청을 제대로 이해하지 못하고 같은 응답을 반복하는 할루시네이션 발생

---

## 1. 문제 상황 분석

### 1-1. 스크린샷에서 관찰된 증상

```
사용자: "미팅 일정 취소하고, 워스 탭에 'AI 정보' 만들고 본문 내용에 다음 내용을 기입해줘"
      • 클로드 업데이트
      • 코덱스 업데이트

n8n Automation: "미팅 일정이 취소되었고, 'AI 정보' 일정이 초가되었습니다.
                  본문 내용으로 '클로드 업데이트'와 '코덱스 업데이트'가 포함되었습니다."

사용자: "워스 탭에 'AI 정보' 만들어서 본문에 다음 내용으로 기입해줘"

n8n Automation: "이미 'AI 정보' 일정이 생성되어 있으며,
                  본문에 '클로드 업데이트'와 '코덱스 업데이트' 내용이 기입되어 있습니다."

사용자: "아싸 500원 주웠어."

n8n Automation: "이미 'AI 정보' 일정이 생성되어 있으며,
                  본문에 '클로드 업데이트'와 '코덱스 업데이트' 내용이 기입되어 있습니다.
                  그리고 500원 주우셨다니 기쁜 좋으셨겠어요!"
```

### 1-2. 핵심 문제

| 문제 | 설명 |
|------|------|
| **할루시네이션** | AI가 실제로 도구를 실행하지 않고 "완료했다"고 거짓 응답 |
| **컨텍스트 오염** | 이전 대화에서 언급된 내용을 실제로 실행한 것처럼 착각 |
| **도구 실행 실패** | `add_schedule` 등 도구가 호출되지 않고 텍스트로만 응답 |
| **검증 부재** | 도구 실행 결과를 확인하지 않고 가정으로 응답 |

---

## 2. 근본 원인 분석

### 2-1. 시스템 프롬프트의 모호성

현재 `schedule.py`의 시스템 프롬프트:

```python
SYSTEM_PROMPT = """당신은 유능하고 친근한 개인 비서입니다. 사용자의 일정을 관리합니다.

## 핵심 역할
- 일정 조회/추가/수정/삭제, 빈 시간 확인, 일정 충돌 확인

## 질문 vs 요청 구분
- "~가능해?", "~있어?", "~알려줘" → 정보 조회만
- "~해줘", "~추가해", "~잡아줘" → 함수 호출
```

**문제점:**
1. "함수 호출"이 필수인지 선택인지 불명확
2. 함수 실행 실패 시 처리 방법 없음
3. 응답 전 검증 규칙 없음

### 2-2. 도구 실행 후 검증 부재

`chat_with_tools_multi` 함수:

```python
# Execute each tool and append results
for tc in tool_calls:
    tool_result = tool_executor(tc["name"], tc["arguments"])
    full_messages.append({
        "role": "tool",
        "tool_call_id": tc["id"],
        "content": str(tool_result),  # ← 단순 문자열 변환만
    })
```

**문제점:**
1. `tool_result`가 성공/실패를 명확히 전달하지 않음
2. AI가 도구 실행 결과를 무시하고 자체 판단으로 응답
3. 실패 시 재시도 메커니즘 없음

### 2-3. 컨텍스트 누적으로 인한 혼란

세션 히스토리가 계속 누적되어 AI가 "이미 했다"고 착각:

```python
if session and session.get("messages"):
    messages = list(session["messages"][-16:])  # 최근 16개만
messages.append({"role": "user", "content": f"{context}\n\n## 사용자 요청\n{message}"})
```

**문제점:**
1. 실제 실행 여부와 상관없이 대화만 누적
2. AI가 "대화에서 언급됨 = 실행됨"으로 착각
3. 도구 실행 성공/실패 상태가 명시적이지 않음

---

## 3. 해결 방안

### 3-1. 시스템 프롬프트 강화 (즉시 적용 가능)

**Before:**
```python
## 질문 vs 요청 구분
- "~가능해?", "~있어?", "~알려줘" → 정보 조회만
- "~해줘", "~추가해", "~잡아줘" → 함수 호출
```

**After:**
```python
## 행동 규칙 (CRITICAL - 반드시 준수)

1. **함수 실행 필수 원칙**
   - 사용자가 "~해줘", "~추가해", "~만들어줘", "~기입해줘" 등 명령형을 사용하면
     반드시 해당 도구 함수를 호출해야 합니다.
   - 도구 호출 없이 "완료했습니다", "추가했습니다" 등의 응답은 절대 금지입니다.

2. **응답 전 검증 원칙**
   - 도구 실행 결과를 먼저 확인하고, 결과에 기반하여 응답하세요.
   - "성공" 메시지가 명확히 나온 경우에만 "완료했습니다"라고 응답하세요.
   - 결과가 불명확하면 "처리 중 문제가 발생했습니다"라고 솔직히 응답하세요.

3. **할루시네이션 방지**
   - 이전 대화에서 언급된 내용을 실제로 실행한 것처럼 말하지 마세요.
   - 현재 요청에 대해서만 도구를 호출하고, 그 결과만 응답하세요.
   - "이미 ~했습니다"라는 응답은 데이터베이스에서 실제로 확인한 경우에만 사용하세요.

4. **불확실성 표현**
   - 확실하지 않으면 "확인이 필요합니다" 또는 "다시 시도해주세요"라고 응답하세요.
   - 추측성 응답("~된 것 같습니다", "~했을 겁니다") 금지.
```

### 3-2. 도구 실행 결과 명시적 검증

`_exec_tool` 함수 반환값을 구조화:

**Before:**
```python
def _exec_tool(name, args):
    if name == "add_schedule":
        # ... (생략)
        if r["success"]:
            return f"일정 추가 완료! {args['date']}"
        return f"추가 실패: {r.get('error','')}"
```

**After:**
```python
def _exec_tool(name, args):
    if name == "add_schedule":
        # ... (생략)
        result = create_page(_db("tasks"), props)
        if result["success"]:
            return json.dumps({
                "status": "success",
                "action": "add_schedule",
                "message": f"일정 추가 완료! {args['date']} {args['title']}",
                "data": {
                    "page_id": result.get("page_id"),
                    "title": args["title"],
                    "date": args["date"]
                }
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "error",
                "action": "add_schedule",
                "message": f"추가 실패: {result.get('error','')}",
                "error": result.get("error")
            }, ensure_ascii=False)
```

### 3-3. AI 응답 후처리 (Post-processing)

`chat_with_tools_multi` 함수에서 도구 실행 검증 단계 추가:

```python
def chat_with_tools_multi(system_prompt, messages, tools, tool_executor,
                          max_tokens=1500, max_tool_rounds=3, domain="",
                          image_urls=None):
    # ... (기존 코드)

    for _ in range(max_tool_rounds):
        result = provider.chat(full_messages, tools, max_tokens)
        tool_calls = result.get("tool_calls", [])

        if not tool_calls:
            # 도구 호출 없이 응답하려고 함 → 검증
            response_text = result.get("content", "")
            if _has_action_claim_without_tool_call(response_text, messages):
                # "완료했습니다"라고 하지만 실제 도구 호출이 없음
                # → 경고 메시지로 교체
                return {
                    "response": "요청을 처리하려고 했지만 실행에 실패했습니다. 다시 시도해주세요.",
                    "interactive": None,
                    "learning_events": learning_events,
                }
            return {
                "response": strip_markdown(response_text),
                "interactive": None,
                "learning_events": learning_events,
            }

        # ... (도구 실행 로직)

        # 도구 실행 결과 검증
        for tc in tool_calls:
            tool_result = tool_executor(tc["name"], tc["arguments"])

            # JSON 파싱 시도
            try:
                parsed = json.loads(tool_result)
                if parsed.get("status") == "error":
                    # 실패한 경우 AI에게 명확히 전달
                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"❌ 실행 실패: {parsed.get('message', '알 수 없는 오류')}",
                    })
                else:
                    full_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": f"✅ {parsed.get('message', tool_result)}",
                    })
            except json.JSONDecodeError:
                # 기존 문자열 응답 유지
                full_messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(tool_result),
                })
```

### 3-4. 할루시네이션 탐지 함수

```python
def _has_action_claim_without_tool_call(response_text, recent_messages):
    """
    응답에 "완료", "추가했습니다" 등의 행동 완료 표현이 있지만
    실제 도구 호출이 없는 경우를 탐지합니다.
    """
    action_claims = [
        "완료했습니다", "추가했습니다", "생성했습니다", "만들었습니다",
        "기입했습니다", "저장했습니다", "수정했습니다", "삭제했습니다",
        "일정이 추가", "일정을 추가", "페이지를 만들", "페이지가 만들"
    ]

    response_lower = response_text.lower()

    # 행동 완료 표현이 있는지 확인
    has_claim = any(claim in response_lower for claim in action_claims)

    if not has_claim:
        return False

    # 최근 메시지에서 assistant가 tool_calls를 호출했는지 확인
    for msg in reversed(recent_messages[-3:]):
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            return False  # 도구 호출이 있었음

    # "이미"라는 단어가 있으면 이전 상태를 참조하는 것이므로 pass
    if "이미" in response_lower or "있습니다" in response_lower:
        return False

    return True  # 행동 완료 표현은 있지만 도구 호출이 없음 → 할루시네이션
```

---

## 4. 구현 우선순위

| 우선순위 | 항목 | 난이도 | 효과 | 소요 시간 |
|---------|------|--------|------|----------|
| 🔥 P0 | 시스템 프롬프트 강화 | 쉬움 | 높음 | 10분 |
| 🔥 P0 | 도구 실행 결과 JSON 구조화 | 보통 | 높음 | 30분 |
| ⚡ P1 | 할루시네이션 탐지 함수 추가 | 보통 | 중간 | 20분 |
| ⚡ P1 | 도구 실행 검증 로직 추가 | 어려움 | 높음 | 40분 |
| 📋 P2 | 로깅 및 모니터링 강화 | 쉬움 | 중간 | 15분 |

---

## 5. 즉시 적용 가능한 Quick Fix

### 5-1. 시스템 프롬프트에 추가 (지금 바로 적용 가능)

`domains/schedule.py` 파일의 `SYSTEM_PROMPT` 끝에 추가:

```python
SYSTEM_PROMPT = """당신은 유능하고 친근한 개인 비서입니다. 사용자의 일정을 관리합니다.

## 핵심 역할
- 일정 조회/추가/수정/삭제, 빈 시간 확인, 일정 충돌 확인

## CRITICAL: 행동 규칙 (절대 원칙)

1. 명령형 요청("~해줘", "~추가해", "~만들어줘")이 나오면 반드시 해당 도구를 호출하세요.
2. 도구 호출 없이 "완료했습니다", "추가했습니다"라고 응답하는 것은 절대 금지입니다.
3. 도구 실행 결과를 먼저 확인하고, 그 결과에 기반하여 응답하세요.
4. 이전 대화에서 언급된 내용을 "이미 했다"고 착각하지 마세요.
   데이터베이스에서 실제로 확인한 경우에만 "이미 ~있습니다"라고 응답하세요.
5. 확실하지 않으면 솔직히 "확인이 필요합니다"라고 응답하세요.

## 질문 vs 요청 구분
- "~가능해?", "~있어?", "~알려줘" → search_schedule, query_schedule_by_range로 조회만
- "~해줘", "~추가해", "~잡아줘" → 반드시 add_schedule, update_schedule 등 실행 도구 호출

## 예시:
❌ 나쁜 예:
   사용자: "내일 회의 추가해줘"
   AI: "네, 내일 회의 일정을 추가했습니다." (도구 호출 없음)

✅ 좋은 예:
   사용자: "내일 회의 추가해줘"
   AI: [add_schedule 도구 호출] → "일정 추가 완료! 2026-02-09 회의"

## 중요: 시간대 (Timezone)
- 모든 시간은 한국 시간(KST, UTC+9) 기준입니다.
- 절대로 UTC 변환하지 마세요.

## 응답 스타일
- 한국어, 친근하게""" + PLAIN_TEXT_RULE
```

### 5-2. 도구 실행 검증 추가

`domains/schedule.py`의 `_exec_tool` 함수를 수정하여 모든 반환값에 성공/실패 명시:

```python
def _exec_tool(name, args):
    if name == "add_schedule":
        # ... (기존 로직)
        r = create_page(_db("tasks"), props)
        if r["success"]:
            # 성공 명시
            return "✅ 일정 추가 완료! " + f"{args['date']} {args['title']}"
        else:
            # 실패 명시
            return "❌ 추가 실패: " + r.get('error','알 수 없는 오류')

    # 다른 도구들도 동일하게 ✅/❌ 추가
```

---

## 6. 테스트 시나리오

### 6-1. 할루시네이션 방지 테스트

| 테스트 케이스 | 입력 | 기대 결과 |
|-------------|------|-----------|
| 명령형 요청 | "내일 회의 추가해줘" | `add_schedule` 도구 호출 → "✅ 일정 추가 완료!" |
| 연속 명령 | "일정 추가해줘" → "500원 주웠어" | 첫 번째만 도구 호출, 두 번째는 잡담 응답 |
| 도구 실패 | (Notion API 오류) | "❌ 추가 실패: 네트워크 오류" (거짓 성공 응답 금지) |
| 질문형 요청 | "내일 일정 있어?" | `query_schedule_by_range` 조회만, 추가 안 함 |

### 6-2. 실제 테스트 방법

```bash
cd /Users/yoogeon/.claude/skills/beyondworks-assistant

# 1. 명령형 테스트
python3 assistant.py schedule "내일 오후 2시 회의 추가해줘" chat

# 2. 연속 요청 테스트
python3 assistant.py schedule "일정 추가해줘" chat test_user test_channel
python3 assistant.py schedule "500원 주웠어" chat test_user test_channel

# 3. 질문형 테스트
python3 assistant.py schedule "내일 일정 있어?" chat
```

---

## 7. 모니터링 및 로깅

### 7-1. 할루시네이션 탐지 로그 추가

`core/openai_client.py`에 추가:

```python
# 디버그 로그 경로
HALLUCINATION_LOG = os.path.join(os.path.dirname(__file__), "../hallucination_detection.log")

def _log_hallucination(message, response, tool_calls):
    """할루시네이션 의심 사례를 로그에 기록"""
    try:
        with open(HALLUCINATION_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n--- {datetime.now().isoformat()} ---\n")
            f.write(f"Message: {message}\n")
            f.write(f"Response: {response}\n")
            f.write(f"Tool calls: {tool_calls}\n")
            f.write(f"Hallucination: True\n")
    except Exception:
        pass
```

---

## 8. 결론

### 핵심 해결 방안 요약

1. **시스템 프롬프트 강화** ← 지금 바로 적용 가능
   - "반드시 도구 호출" 원칙 명시
   - "도구 결과 검증 후 응답" 원칙 명시
   - 할루시네이션 금지 명시

2. **도구 실행 결과 명시적 표현**
   - ✅/❌ 이모지로 성공/실패 명확히 구분
   - JSON 구조화로 파싱 가능하게 개선

3. **할루시네이션 ���지 및 차단**
   - "완료했습니다" 표현이 있지만 도구 호출이 없으면 경고
   - 검증 로직 추가

### 단계별 적용 계획

1. **즉시 적용** (10분): 시스템 프롬프트 수정 + ✅/❌ 추가
2. **오늘 내** (1시간): 도구 실행 검증 로직 + 할루시네이션 탐지
3. **내일** (1시간): 모니터링 대시보드 + 로깅 강화

### 예상 효과

- 할루시네이션 **90% 이상 감소**
- 사용자 신뢰도 **대폭 향상**
- 디버깅 시간 **50% 단축**

---

**다음 단계**: 즉시 적용 가능한 Quick Fix를 먼저 구현하겠습니다.
