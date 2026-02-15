"""Schedule domain handler — 일정/업무 관리"""
import json
from datetime import datetime, timedelta
from core.config import get_domain_config
from core.notion_client import query_database, create_page, update_page, archive_page, parse_page_properties
from core.openai_client import (
    chat_completion,
    chat_with_tools_multi,
    REQUEST_USER_CHOICE_TOOL,
    LEARN_RULE_TOOL,
)
from core.memory import get_rules_as_prompt

DOMAIN = "schedule"
CFG = None

PLAIN_TEXT_RULE = "\n\n## 응답 규칙\n- 반드시 플레인 텍스트로 응답. **bold**, [link](url), # heading, `code` 등 마크다운 절대 금지.\n- 이모지 사용 가능."


def _cfg():
    global CFG
    if CFG is None:
        CFG = get_domain_config(DOMAIN)
    return CFG


def _db(key):
    return _cfg().get("databases", {}).get(key, "")


SYSTEM_PROMPT = """당신은 유능하고 친근한 개인 비서입니다. 사용자의 일정을 관리합니다.

## 핵심 역할
- 일정 조회/추가/수정/삭제, 빈 시간 확인, 일정 충돌 확인

## ⚠️ CRITICAL: 행동 규칙 (절대 원칙 - 반드시 준수) ⚠️

### 🚨 규칙 1: 명령형 = 도구 호출 필수 (예외 없음)
사용자가 다음 표현을 사용하면 **100% 반드시** 도구를 호출해야 합니다:
- "~해줘", "~추가해", "~만들어줘", "~기입해줘", "~잡아줘", "~등록해줘"

**절대 금지**: 도구 호출 없이 "완료했습니다", "추가했습니다", "생성했습니다" 등의 응답
→ 이렇게 응답하면 시스템 오류로 간주되어 사용자에게 경고 메시지가 표시됩니다.

**올바른 흐름**:
1. 명령형 요청 감지
2. 필수 정보 확인 (날짜, 시간 등)
3. 정보 부족하면 request_user_choice로 선택지 제시
4. 정보 충분하면 즉시 add_schedule/update_schedule/delete_schedule 호출
5. 도구 결과 확인 후 응답

### 🚨 규칙 2: 응답 전 도구 실행 결과 확인
- 도구 결과에 "✅"가 있을 때만 "완료했습니다"라고 응답
- 도구 결과에 "❌"가 있으면 "실패했습니다"라고 솔직히 응답
- 도구를 호출하지 않았다면 "~했습니다" 표현 절대 금지

### 🚨 규칙 3: 할루시네이션 절대 금지
- 이전 대화 내용을 실제 실행한 것처럼 말하지 마세요
- "이미 ~했습니다"는 search_schedule 도구로 DB에서 확인한 경우에만 사용
- 확실하지 않으면 "확인이 필요합니다" 또는 도구 호출

## 📝 올바른 처리 예시

**예시 1: 기본 일정 추가**
```
사용자: "내일 오후 2시 회의 추가해줘"
AI 처리:
  1. 명령형 감지: "추가해줘" → add_schedule 도구 필수
  2. 정보 추출: 날짜=내일, 시간=14:00, 제목=회의
  3. add_schedule 호출
  4. 결과: "✅ 일정 추가 완료! 2026-02-09 14:00 회의"
응답: "일정 추가 완료! 내일 오후 2시에 회의가 등록되었습니다."
```

**예시 2: 정보 부족 시**
```
사용자: "회의 추가해줘"
AI 처리:
  1. 명령형 감지: "추가해줘" → add_schedule 필요
  2. 날짜 정보 없음 → request_user_choice 호출
응답: "언제 회의를 추가할까요?"
선택지: ["오늘", "내일", "모레", "다음 주 월요일"]
```

**예시 3: 질문형 요청**
```
사용자: "내일 일정 있어?"
AI 처리:
  1. 질문형 감지: "있어?" → 조회만
  2. query_schedule_by_range 호출
  3. 결과 반환
응답: "내일(2026-02-09) 일정: ..."
```

## ❌ 절대 하지 말아야 할 응답 (시스템 오류)

```
사용자: "내일 회의 추가해줘"
AI (잘못된 응답): "네, 내일 회의 일정을 추가했습니다."
→ 🚨 오류: add_schedule 도구 호출 없음 → 시스템이 "실행 실패" 경고 표시
```

```
사용자: "워크스페이스에 AI 정보 추가해줘"
AI (잘못된 응답): "이미 AI 정보 일정이 추가되어 있습니다."
→ 🚨 오류: search_schedule로 확인하지 않고 추측 → 할루시네이션
```

## 💡 핵심 원칙 요약
1. 명령형("~해줘") = 반드시 도구 호출
2. 도구 결과 확인 후 응답
3. 확실하지 않으면 솔직히 말하거나 도구로 확인

## 질문 vs 요청 구분
- "~가능해?", "~있어?", "~알려줘" → search_schedule, query_schedule_by_range로 조회만
- "~해줘", "~추가해", "~잡아줘", "~만들어줘" → 반드시 add_schedule, update_schedule 등 실행 도구 호출

## 일정 조회 시 완료 항목 포함 규칙
- "오늘 일정" 질문에는 완료된 일정(Completed: True)도 **반드시 포함**하여 응답
- 완료된 일정은 "(완료)" 표시를 붙여서 안내
- 컨텍스트의 [오늘 요약]에 이미 완료/미완료가 구분되어 있으므로 그대로 전달

## 중요: 시간대 (Timezone)
- 모든 시간은 한국 시간(KST, UTC+9) 기준입니다.
- 컨텍스트에 표시된 current_time은 KST입니다.
- 사용자가 "오전 10시"라고 하면 KST 10:00 = HH:MM 형식으로 "10:00"입니다.
- 절대로 UTC 변환하지 마세요. 사용자가 말한 시간을 그대로 HH:MM으로 전달하세요.
- 예: "오전 10시" → time: "10:00", "오후 3시" → time: "15:00"

## 날짜/시간 해석
- "내일" → 내일, "모레" → 모레, "다음 주 월요일" → 계산
- "오후 2시" → 14:00, "아침 9시" → 09:00

## 누락 정보 처리
- 일정 추가 시 날짜나 시간이 누락되면, request_user_choice 도구를 사용하여 선택지를 제시하세요.

## 응답 스타일
- 한국어, 친근하게""" + PLAIN_TEXT_RULE

TOOLS = [
    {"type": "function", "function": {
        "name": "add_schedule",
        "description": "새 일정 추가 (명령형일 때만)",
        "parameters": {"type": "object", "properties": {
            "title": {"type": "string"}, "date": {"type": "string", "description": "YYYY-MM-DD"},
            "time": {"type": "string", "description": "HH:MM"}, "location": {"type": "string"},
            "members": {"type": "string"}, "notes": {"type": "string"}
        }, "required": ["title", "date"]}
    }},
    {"type": "function", "function": {
        "name": "update_schedule", "description": "일정 수정",
        "parameters": {"type": "object", "properties": {
            "page_id": {"type": "string"}, "title": {"type": "string"},
            "date": {"type": "string"}, "time": {"type": "string"},
            "done": {"type": "boolean"}, "notes": {"type": "string"}, "location": {"type": "string"}
        }, "required": ["page_id"]}
    }},
    {"type": "function", "function": {
        "name": "delete_schedule", "description": "일정 삭제",
        "parameters": {"type": "object", "properties": {
            "page_id": {"type": "string"}
        }, "required": ["page_id"]}
    }},
    {"type": "function", "function": {
        "name": "search_schedule", "description": "키워드로 일정 검색",
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string"}
        }, "required": ["keyword"]}
    }},
    {"type": "function", "function": {
        "name": "query_schedule_by_range",
        "description": "특정 날짜 범위의 일정 조회. '지난 3일', '2월 3일~5일', '저번주' 등 과거/미래 일정을 조회할 때 사용.",
        "parameters": {"type": "object", "properties": {
            "start_date": {"type": "string", "description": "시작일 YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "종료일 YYYY-MM-DD"}
        }, "required": ["start_date", "end_date"]}
    }}
]


def _to_kst_range(date_str):
    """날짜 문자열을 KST 하루 범위(00:00~23:59)로 변환.
    Notion API는 UTC 기준 필터링이므로, KST 시간대를 명시해야
    오전 9시 이전 일정(UTC 기준 전날)이 누락되지 않음."""
    return f"{date_str}T00:00:00+09:00", f"{date_str}T23:59:59+09:00"


def _query_by_date(date_str):
    start, end = _to_kst_range(date_str)
    return query_database(_db("tasks"),
        filter_obj={"and": [
            {"property": "Date", "date": {"on_or_after": start}},
            {"property": "Date", "date": {"on_or_before": end}}
        ]},
        sorts=[{"property": "Date", "direction": "ascending"}])


def _query_by_range(start_date, end_date):
    start = f"{start_date}T00:00:00+09:00"
    end = f"{end_date}T23:59:59+09:00"
    return query_database(_db("tasks"),
        filter_obj={"and": [
            {"property": "Date", "date": {"on_or_after": start}},
            {"property": "Date", "date": {"on_or_before": end}}
        ]}, sorts=[{"property": "Date", "direction": "ascending"}])


def _query_incomplete():
    return query_database(_db("tasks"),
        filter_obj={"property": "Completed", "checkbox": {"equals": False}},
        sorts=[{"property": "Date", "direction": "ascending"}])


def _search(keyword):
    return query_database(_db("tasks"),
        filter_obj={"property": "Entry name", "title": {"contains": keyword}},
        sorts=[{"property": "Date", "direction": "descending"}])


def _results_to_list(qr):
    if isinstance(qr, dict):
        return [parse_page_properties(p) for p in qr.get("results", [])]
    return qr


def _get_context():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    tomorrow = now + timedelta(days=1)
    week_start = now - timedelta(days=now.weekday())
    week_end = now + timedelta(days=(6 - now.weekday()))
    next_week_start = week_end + timedelta(days=1)
    next_week_end = next_week_start + timedelta(days=6)
    last_week_start = week_start - timedelta(days=7)
    last_week_end = week_start - timedelta(days=1)

    # 요일별 날짜 매핑 (AI가 계산 안 하도록 명시)
    day_names = ['월', '화', '수', '목', '금', '토', '일']
    this_week_days = {f"{day_names[i]}요일": (week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)}
    next_week_days = {f"{day_names[i]}요일": (next_week_start + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7)}

    return {
        "current_time": now.strftime('%Y-%m-%d %H:%M'),
        "weekday": day_names[now.weekday()],
        "last_week": _results_to_list(_query_by_range(last_week_start.strftime('%Y-%m-%d'), last_week_end.strftime('%Y-%m-%d'))),
        "yesterday": _results_to_list(_query_by_date(yesterday.strftime('%Y-%m-%d'))),
        "today": _results_to_list(_query_by_date(now.strftime('%Y-%m-%d'))),
        "tomorrow": _results_to_list(_query_by_date(tomorrow.strftime('%Y-%m-%d'))),
        "this_week": _results_to_list(_query_by_range(now.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))),
        "next_week": _results_to_list(_query_by_range(next_week_start.strftime('%Y-%m-%d'), next_week_end.strftime('%Y-%m-%d'))),
        "incomplete": _results_to_list(_query_incomplete()),
        "dates": {
            "last_week": f"{last_week_start.strftime('%Y-%m-%d')}~{last_week_end.strftime('%Y-%m-%d')}",
            "yesterday": yesterday.strftime('%Y-%m-%d'),
            "today": now.strftime('%Y-%m-%d'),
            "tomorrow": tomorrow.strftime('%Y-%m-%d'),
            "this_week": f"{week_start.strftime('%Y-%m-%d')}~{week_end.strftime('%Y-%m-%d')}",
            "next_week": f"{next_week_start.strftime('%Y-%m-%d')}~{next_week_end.strftime('%Y-%m-%d')}",
        },
        "this_week_days": this_week_days,
        "next_week_days": next_week_days,
    }


def _exec_tool(name, args):
    if name == "add_schedule":
        date_str = args["date"]
        if args.get("time"):
            date_val = {"start": f"{date_str}T{args['time']}:00+09:00"}
        elif "T" in date_str and "+09:00" not in date_str and "+" not in date_str.split("T")[1]:
            date_val = {"start": f"{date_str}+09:00"}
        else:
            date_val = {"start": date_str}
        props = {
            "Entry name": {"title": [{"text": {"content": args["title"]}}]},
            "Date": {"date": date_val},
            "Completed": {"checkbox": False},
            "Relation": {"relation": [{"id": _cfg().get("schedule_relation_id", "")}]}
        }
        if args.get("notes"):
            props["Notes"] = {"rich_text": [{"text": {"content": args["notes"]}}]}
        if args.get("location"):
            props["Location (Entry)"] = {"rich_text": [{"text": {"content": args["location"]}}]}
        if args.get("members"):
            props["Members"] = {"rich_text": [{"text": {"content": args["members"]}}]}
        r = create_page(_db("tasks"), props)
        if r["success"]:
            parts = [f"✅ 일정 추가 완료! {args['date']}"]
            if args.get("time"):
                parts.append(f"{args['time']}")
            parts.append(f"{args['title']}")
            if args.get("location"):
                parts.append(f"장소: {args['location']}")
            return "\n".join(parts)
        return f"❌ 추가 실패: {r.get('error','알 수 없는 오류')}"

    if name == "update_schedule":
        pid = args.pop("page_id")
        props = {}
        if "title" in args:
            props["Entry name"] = {"title": [{"text": {"content": args["title"]}}]}
        if "date" in args:
            date_str = args["date"]
            if args.get("time"):
                dv = {"start": f"{date_str}T{args['time']}:00+09:00"}
            elif "T" in date_str and "+09:00" not in date_str and "+" not in date_str.split("T")[1]:
                # AI가 ISO 형식으로 보냈지만 timezone 없으면 KST 추가
                dv = {"start": f"{date_str}+09:00" if not date_str.endswith("+09:00") else date_str}
            else:
                dv = {"start": date_str}
            props["Date"] = {"date": dv}
        if "done" in args:
            props["Completed"] = {"checkbox": args["done"]}
        if "notes" in args:
            props["Notes"] = {"rich_text": [{"text": {"content": args["notes"]}}]}
        if "location" in args:
            props["Location (Entry)"] = {"rich_text": [{"text": {"content": args["location"]}}]}
        r = update_page(pid, props)
        return "✅ 수정 완료!" if r["success"] else f"❌ 수정 실패: {r.get('error','알 수 없는 오류')}"

    if name == "delete_schedule":
        r = archive_page(args["page_id"])
        return "✅ 삭제 완료!" if r["success"] else f"❌ 삭제 실패: {r.get('error','알 수 없는 오류')}"

    if name == "search_schedule":
        results = _results_to_list(_search(args["keyword"]))
        if results:
            lines = [f"'{args['keyword']}' 검색 결과:"]
            for s in results[:10]:
                lines.append(f"- {s.get('Entry name','')} ({s.get('Date','')})")
            return "\n".join(lines)
        return f"'{args['keyword']}' 관련 일정을 찾지 못했어요."

    if name == "query_schedule_by_range":
        results = _results_to_list(_query_by_range(args["start_date"], args["end_date"]))
        if results:
            lines = [f"{args['start_date']} ~ {args['end_date']} 일정:"]
            for s in results[:20]:
                date_val = s.get("Date", "")
                if isinstance(date_val, dict):
                    date_val = date_val.get("start", "")
                title = s.get("Entry name", "")
                notes = s.get("Notes", "")
                done = s.get("Completed", False)
                line = f"- [{date_val}] {title}"
                if done:
                    line += " (완료)"
                if notes:
                    line += f" | 메모: {notes[:50]}"
                lines.append(line)
            return "\n".join(lines)
        return f"{args['start_date']} ~ {args['end_date']} 기간에 일정이 없습니다."

    return "알 수 없는 도구"


def _briefing(ctx, mode):
    today_done = [s for s in ctx['today'] if s.get('Completed')]
    today_pending = [s for s in ctx['today'] if not s.get('Completed')]
    yesterday_pending = [s for s in ctx['yesterday'] if not s.get('Completed')]

    if mode == "morning_briefing":
        prompt = (
            "오전 브리핑을 작성하세요. 플레인 텍스트, 이모지 사용, 한국어.\n"
            "구성: 1) 인사 2) 어제 놓친 일(미완료) 리마인드 3) 오늘 할 일 목록 4) 응원 한마디"
        )
        content = (
            f"오늘: {ctx['dates']['today']} ({ctx['weekday']}요일)\n"
            f"어제 미완료 ({len(yesterday_pending)}건): {json.dumps(yesterday_pending[:5], ensure_ascii=False)}\n"
            f"오늘 할 일 ({len(today_pending)}건): {json.dumps(today_pending[:10], ensure_ascii=False)}\n"
            f"전체 미완료 ({len(ctx['incomplete'])}건): {json.dumps(ctx['incomplete'][:5], ensure_ascii=False)}"
        )
    elif mode == "evening_briefing":
        prompt = (
            "오후 브리핑을 작성하세요. 플레인 텍스트, 이모지 사용, 한국어.\n"
            "구성: 1) 오늘 완료한 일 회고 + 칭찬 2) 아직 미완료인 일 3) 내일 일정 미리보기 4) 마무리 인사"
        )
        content = (
            f"오늘: {ctx['dates']['today']} ({ctx['weekday']}요일)\n"
            f"오늘 완료 ({len(today_done)}건): {json.dumps(today_done[:10], ensure_ascii=False)}\n"
            f"오늘 미완료 ({len(today_pending)}건): {json.dumps(today_pending[:10], ensure_ascii=False)}\n"
            f"내일 일정: {json.dumps(ctx['tomorrow'][:10], ensure_ascii=False)}"
        )
    elif mode == "daily_briefing":
        # 레거시 호환: morning_briefing과 동일하게 동작
        prompt = (
            "오전 브리핑을 작성하세요. 플레인 텍스트, 이모지 사용, 한국어.\n"
            "구성: 1) 인사 2) 어제 놓친 일(미완료) 리마인드 3) 오늘 할 일 목록 4) 응원 한마디"
        )
        content = (
            f"오늘: {ctx['dates']['today']} ({ctx['weekday']}요일)\n"
            f"어제 미완료 ({len(yesterday_pending)}건): {json.dumps(yesterday_pending[:5], ensure_ascii=False)}\n"
            f"오늘 할 일 ({len(today_pending)}건): {json.dumps(today_pending[:10], ensure_ascii=False)}\n"
            f"전체 미완료 ({len(ctx['incomplete'])}건): {json.dumps(ctx['incomplete'][:5], ensure_ascii=False)}"
        )
    elif mode == "weekly_briefing":
        prompt = "주간 브리핑: 이번 주 일정 요약, 미완료 항목, 주의사항. 이모지 사용. 한국어."
        content = f"이번 주: {json.dumps(ctx['this_week'], ensure_ascii=False)}\n다음 주: {json.dumps(ctx['next_week'], ensure_ascii=False)}\n미완료: {json.dumps(ctx['incomplete'][:10], ensure_ascii=False)}"
    else:
        return None
    return chat_completion([{"role": "system", "content": prompt + PLAIN_TEXT_RULE}, {"role": "user", "content": content}], max_tokens=800, temperature=0.5)


def _reminder(ctx):
    now = datetime.now()
    reminders = []
    # (목표 분, 허용 오차 ±분, 라벨)
    thresholds = [
        (180, 1, "3시간"),
        (60, 1, "1시간"),
        (30, 1, "30분"),
        (10, 1, "10분"),
    ]
    for s in ctx["today"]:
        if s.get("Completed"):
            continue
        date_val = s.get("Date", "")
        if isinstance(date_val, dict):
            date_val = date_val.get("start", "")
        if "T" not in str(date_val):
            continue
        try:
            tp = str(date_val).split("T")[1][:5]
            h, m = map(int, tp.split(":"))
            event_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
            diff = (event_time - now).total_seconds() / 60
            for target, tolerance, label in thresholds:
                if target - tolerance <= diff <= target + tolerance:
                    reminders.append(f"{label} 전: {s.get('Entry name','')} ({tp})")
                    break
        except Exception:
            pass
    return "\n".join(reminders) if reminders else None


def handle(message, mode="chat", session=None, image_urls=None):
    ctx = _get_context()

    if mode in ("daily_briefing", "morning_briefing", "evening_briefing", "weekly_briefing"):
        resp = _briefing(ctx, mode)
        return {"response": resp, "domain": DOMAIN}

    if mode == "reminder":
        resp = _reminder(ctx)
        return {"response": resp, "has_reminder": resp is not None, "domain": DOMAIN}

    if not message:
        return {"error": "메시지가 필요합니다", "domain": DOMAIN}

    # 요일-날짜 매핑 문자열 생성
    tw = ctx['this_week_days']
    nw = ctx['next_week_days']
    tw_map = ", ".join(f"{k}={v}" for k, v in tw.items())
    nw_map = ", ".join(f"{k}={v}" for k, v in nw.items())

    # 오늘 일정을 완료/미완료로 사전 분류 (AI가 완료 항목을 무시 못하게 코드 방어)
    today_done = [s for s in ctx['today'] if s.get('Completed')]
    today_pending = [s for s in ctx['today'] if not s.get('Completed')]
    today_summary = f"총 {len(ctx['today'])}건 (미완료 {len(today_pending)}건, 완료 {len(today_done)}건)"

    # 각 시간대별 방어 헤더 생성 (AI가 다른 섹션의 항목을 혼동하지 못하게)
    def _section_summary(items, max_names=5):
        n = len(items)
        if n == 0:
            return "0건"
        names = ", ".join(s.get('Entry name', '?') for s in items[:max_names])
        suffix = f" 외 {n - max_names}건" if n > max_names else ""
        return f"{n}건: {names}{suffix}"

    yesterday_summary = _section_summary(ctx['yesterday'])
    tomorrow_summary = _section_summary(ctx['tomorrow'])
    last_week_summary = f"{len(ctx['last_week'])}건"
    this_week_summary = f"{len(ctx['this_week'])}건"
    next_week_summary = f"{len(ctx['next_week'])}건"

    context = f"""## 현재 {ctx['current_time']} KST ({ctx['weekday']}요일) — 모든 시간은 한국 시간(KST), 2026년 기준
## 날짜 참조: 지난주={ctx['dates']['last_week']} 어제={ctx['dates']['yesterday']} 오늘={ctx['dates']['today']} 내일={ctx['dates']['tomorrow']} 이번주={ctx['dates']['this_week']} 다음주={ctx['dates']['next_week']}
## 이번 주 요일→날짜: {tw_map}
## 다음 주 요일→날짜: {nw_map}
## CRITICAL: "이번 주 일요일"은 위 매핑표에서 이번 주 일요일 날짜를 그대로 사용. 절대 직접 계산하지 마세요.
## CRITICAL: 각 섹션의 일정 데이터만 해당 기간의 일정입니다. 다른 섹션의 항목을 섞어서 답하지 마세요.
## 지난주 일정 [{last_week_summary}]
{json.dumps(ctx['last_week'][:15], ensure_ascii=False, indent=1)}
## 어제 일정 [{yesterday_summary}] — 이 리스트에 없는 항목을 어제 일정이라고 말하지 마세요
{json.dumps(ctx['yesterday'][:10], ensure_ascii=False, indent=1)}
## 오늘 일정 [{today_summary}] — 완료 항목도 반드시 사용자에게 안내할 것
### 미완료 ({len(today_pending)}건)
{json.dumps(today_pending[:10], ensure_ascii=False, indent=1)}
### 완료 ({len(today_done)}건)
{json.dumps(today_done[:10], ensure_ascii=False, indent=1)}
## 내일 일정 [{tomorrow_summary}]
{json.dumps(ctx['tomorrow'][:10], ensure_ascii=False, indent=1)}
## 이번 주 남은 일정 [{this_week_summary}]
{json.dumps(ctx['this_week'][:15], ensure_ascii=False, indent=1)}
## 다음 주 일정 [{next_week_summary}]
{json.dumps(ctx['next_week'][:15], ensure_ascii=False, indent=1)}
## 미완료
{json.dumps(ctx['incomplete'][:10], ensure_ascii=False, indent=1)}"""

    # Build messages from session history
    messages = []
    if session and session.get("messages"):
        messages = list(session["messages"][-16:])
    messages.append({"role": "user", "content": f"{context}\n\n## 사용자 요청\n{message}"})

    learned_rules = get_rules_as_prompt(DOMAIN)

    # 명령형 요청 감지 (도구 호출 강제)
    is_command = any(word in message.lower() for word in ["해줘", "추가해", "만들어줘", "기입해줘", "잡아줘", "등록해줘", "수정해", "삭제해", "지워줘"])

    result = chat_with_tools_multi(
        SYSTEM_PROMPT + learned_rules, messages,
        TOOLS + [REQUEST_USER_CHOICE_TOOL, LEARN_RULE_TOOL], _exec_tool,
        domain=DOMAIN, image_urls=image_urls,
        force_tool_call=is_command  # 명령형이면 도구 호출 강제
    )

    output = {
        "response": result["response"],
        "domain": DOMAIN,
        "learning_events": result.get("learning_events", []),
    }
    if result.get("interactive"):
        output["interactive"] = result["interactive"]
    return output
