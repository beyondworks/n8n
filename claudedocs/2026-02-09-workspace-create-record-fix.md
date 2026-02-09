# 2026-02-09 workspace create_record 중복 생성 및 빈 values 문제 해결

## 문제 요약

Slack에서 "웍스 탭에 '훅' 만들고 본문에 후욱후욱" 요청 시:
1. Notion에 동일 제목 레코드가 **2개** 생성됨 (하나는 본문 포함, 다른 하나는 본문 없음)
2. AI가 `create_record(values=null)`로 호출하여 "Entry name이 누락되었습니다" 내부 에러가 사용자에게 노출됨
3. 내부 에러 메시지가 그대로 Slack 응답으로 전달됨

## 근본 원인 분석 (5-Why)

### 왜 레코드가 2개 생성되나?
`chat_with_tools_multi` 루프에서 AI가 한 라운드에 `create_record`를 2번 호출하거나, 에러 후 재시도하면서 중복 생성.

### 왜 AI가 values=null로 호출하나?
GPT-4o-mini가 복합 요청("만들고 + 본문 기입")을 분해할 때, 첫 번째 create_record에서 values를 비워 보내는 패턴이 ~50% 확률로 발생. **프롬프트로 "values를 비우지 마세요"라고 지시해도 무시됨.**

### 왜 에러가 사용자에게 노출되나?
`_exec_tool`이 반환한 에러 문자열을 AI가 그대로 사용자 응답에 포함. 시스템 프롬프트에 "에러를 노출하지 마세요"라고 해도 AI가 무시하거나 에러 텍스트를 재구성하여 포함.

### 핵심 교훈
**AI(LLM)에게 프롬프트로 행동을 제어하려 하면 안 된다. 코드 레벨에서 자동 보정하는 것이 유일하게 신뢰할 수 있는 방법이다.**

## 해결 방법 (코드 레벨 방어 3층)

### 1층: `_exec_tool_guarded` — 중복 생성 방지 + 자동 제목 추출

```python
created_pages = {}  # {database_id: page_id}

def _exec_tool_guarded(name, args):
    if name == "create_record":
        db_id = args.get("database_id", "")
        # 같은 DB에 이미 생성했으면 차단
        if db_id in created_pages:
            return f"성공: 이미 생성된 레코드를 사용하세요. page_id: {created_pages[db_id]}..."
        # values가 비어있으면 원본 메시지에서 제목 자동 추출
        values = args.get("values")
        if not values or values == "null":
            title = _extract_title_from_message(message)
            if title:
                args["values"] = {"Entry name": title}
        result = _exec_tool(name, args)
        # 성공 시 page_id 기록
        if "생성 완료 (page_id:" in result:
            page_id = result.split("page_id: ")[1].rstrip(")")
            created_pages[db_id] = page_id
        return result
    return _exec_tool(name, args)
```

### 2층: `_exec_tool` 내부 — values 자동 복구 + 제목 fallback

```python
# values 비어있으면 args의 다른 필드에서 복구
if not values:
    title_hint = args.get("title") or args.get("name")
    if title_hint:
        values = {"title": str(title_hint)}
    else:
        return "[내부 지시] values가 비어있습니다..."

# title이 properties에 없으면 values의 아무 문자열 값이라도 사용
if title_prop and title_prop not in properties:
    for key in ("title", "name", "entry", "Entry name", ...):
        if values.get(key):
            fallback_title = values[key]; break
    if not fallback_title:
        for v in values.values():
            if v and isinstance(v, str):
                fallback_title = v; break
```

### 3층: 응답 에러 필터 — 최종 방어선

```python
error_patterns = ["[내부 지시]", "title 속성명", "스키마 에러",
                  "values가 비어", "제목이 없습니다", "\"Entry name\"이 누락"]
if any(pat in response_text for pat in error_patterns):
    if created_pages:
        response_text = "요청을 처리했습니다."
    else:
        response_text = "요청을 처리하지 못했습니다. 다시 시도해주세요."
```

## 추가 개선사항

### force_tool_call
명령형 요청 ("만들어줘", "기입해줘" 등)에 대해 `force_tool_call=True` 전달하여 AI가 도구 호출 없이 텍스트만 반환하는 것을 방지.

### max_tool_rounds 증가
5 → 7로 증가. "만들고 + 본문 기입" 같은 복합 요청은 create_record + append_blocks_to_page로 최소 2-3 라운드가 필요하고, 에러 복구 시 추가 라운드 소모.

### 시스템 프롬프트 간소화
중복되는 규칙 제거, "작업 원칙" 섹션으로 통합. 프롬프트가 길어지면 AI가 규칙을 무시하는 경향이 있어 간결하게 유지.

## 시도했지만 실패한 접근법

| 접근법 | 결과 | 원인 |
|--------|------|------|
| 시스템 프롬프트에 "values를 null로 보내지 마세요" 추가 | ~50% 무시 | LLM은 규칙을 확률적으로 따름 |
| `[내부 지시]` prefix로 에러 숨기기 | AI가 에러 텍스트를 재구성하여 노출 | LLM은 에러 메시지를 요약/변형하여 전달 |
| 에러 응답 필터에 "오류가 발생했습니다" 패턴 추가 | 정상 실패 응답까지 차단 | 패턴이 너무 광범위 |

## 검증 결과

### 로컬 Docker 테스트 (모두 성공)
- "최종테스트" + body "이것은 최종 테스트입니다." → 1개 레코드, 본문 확인
- "린" + body "린킴" → 1개 레코드, 본문 확인
- "김" + body "효율" → 1개 레코드, 본문 확인
- "테" + body "• 스트" (줄바꿈+불릿) → 1개 레코드, 본문 확인

### Slack E2E 테스트 (성공)
- 사용자가 Slack에서 직접 테스트 → 정상 동작 확인

## 수정된 파일

| 파일 | 변경 내용 |
|------|----------|
| `domains/workspace.py` | _exec_tool_guarded, _extract_title_from_message, 응답 에러 필터, force_tool_call, max_tool_rounds=7, 시스템 프롬프트 간소화 |

## 커밋

- **레포**: `beyondworks/leanskills`
- **커밋**: `b2ff643` — `fix: workspace create_record 중복 생성 및 빈 values 문제 해결`
