"""Tools & Resources domain handler — 도구/리소스 관리"""
import json
from datetime import datetime
from core.config import get_domain_config
from core.notion_client import query_database, parse_page_properties
from core.openai_client import (
    chat_completion,
    chat_with_tools_multi,
    REQUEST_USER_CHOICE_TOOL,
    LEARN_RULE_TOOL,
)
from core.memory import get_rules_as_prompt

DOMAIN = "tools"

PLAIN_TEXT_RULE = "\n\n## 응답 규칙\n- 반드시 플레인 텍스트로 응답. **bold**, [link](url), # heading, `code` 등 마크다운 절대 금지.\n- 이모지 사용 가능."


def _cfg():
    return get_domain_config(DOMAIN)


def _db(key):
    return _cfg().get("databases", {}).get(key, "")


SYSTEM_PROMPT = """당신은 도구/리소스 관리 비서입니다. 업무 도구, 구독 서비스, API 키를 관리합니다.

## 역할
- 도구 검색 (카테고리별: AI, Design, Build, Marketing, Source)
- 구독 서비스 현황 및 비용 조회
- API 키/계정 정보 조회
- 결제일 알림

## 응답 스타일
- 한국어, 간결하게""" + PLAIN_TEXT_RULE

TOOLS = [
    {"type": "function", "function": {
        "name": "search_tools",
        "description": "카테고리/키워드로 도구 검색",
        "parameters": {"type": "object", "properties": {
            "category": {"type": "string", "description": "ai, design, build, marketing, source, work 중 택1"},
            "keyword": {"type": "string"}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_subscriptions",
        "description": "구독 서비스 목록 및 결제일 조회",
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string", "description": "서비스명 키워드"}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_subscription_cost",
        "description": "월간/연간 구독 비용 합계",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "get_api_keys",
        "description": "API 키/계정 정보 조회",
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string", "description": "서비스명 키워드"}
        }}
    }}
]

CATEGORY_DB_MAP = {
    "ai": "tool_ai", "design": "tool_design", "build": "tool_build",
    "marketing": "tool_marketing", "source": "tool_source",
    "account": "tool_account", "work": "work_tool"
}


def _query_tools(db_key, keyword=None, limit=15):
    db_id = _db(db_key)
    if not db_id:
        return []
    filt = None
    if keyword:
        filt = {"property": "Entry name", "title": {"contains": keyword}}
    r = query_database(db_id, filter_obj=filt, page_size=limit)
    if isinstance(r, dict) and r.get("success"):
        return [parse_page_properties(p) for p in r.get("results", [])]
    return []


def _query_subscriptions(keyword=None):
    db_id = _db("subscribe")
    if not db_id:
        return []
    filt = None
    if keyword:
        filt = {"property": "Entry name", "title": {"contains": keyword}}
    r = query_database(db_id, filter_obj=filt,
                       sorts=[{"property": "Entry name", "direction": "ascending"}],
                       page_size=50)
    if isinstance(r, dict) and r.get("success"):
        return [parse_page_properties(p) for p in r.get("results", [])]
    return []


def _query_api_archive(keyword=None):
    db_id = _db("api_archive")
    if not db_id:
        return []
    filt = None
    if keyword:
        filt = {"property": "Entry name", "title": {"contains": keyword}}
    r = query_database(db_id, filter_obj=filt, page_size=20)
    if isinstance(r, dict) and r.get("success"):
        return [parse_page_properties(p) for p in r.get("results", [])]
    return []


def _exec_tool(name, args):
    if name == "search_tools":
        cat = args.get("category", "").lower()
        kw = args.get("keyword", "")
        if cat and cat in CATEGORY_DB_MAP:
            results = _query_tools(CATEGORY_DB_MAP[cat], kw)
        elif kw:
            results = []
            for db_key in ["work_tool", "tool_ai", "tool_design", "tool_build", "tool_marketing"]:
                results.extend(_query_tools(db_key, kw, 5))
        else:
            results = _query_tools("work_tool", limit=10)

        if results:
            lines = [f"도구 검색 결과 ({len(results)}건):"]
            for t in results[:15]:
                tool_name = t.get("Entry name", t.get("Name", t.get("이름", "")))
                url = t.get("URL", "")
                desc = t.get("Description", t.get("설명", ""))
                tags = t.get("Tags", [])
                tag_str = " ".join(f"#{tg}" for tg in tags[:3]) if isinstance(tags, list) and tags else ""
                line = f"- {tool_name}"
                if desc:
                    line += f": {desc[:50]}"
                if tag_str:
                    line += f" {tag_str}"
                if url:
                    line += f" ({url})"
                lines.append(line)
            return "\n".join(lines)
        return "도구를 찾을 수 없습니다."

    if name == "get_subscriptions":
        kw = args.get("keyword")
        subs = _query_subscriptions(kw)
        if subs:
            lines = [f"구독 서비스 ({len(subs)}건):"]
            for s in subs:
                sub_name = s.get("Entry name", s.get("Name", ""))
                cost = s.get("Monthly Fee", s.get("Cost", s.get("비용", 0))) or 0
                plan = s.get("Plan", s.get("플랜", ""))
                status = s.get("Status", s.get("상태", ""))
                payment_date = s.get("Payment Date", s.get("결제일", ""))
                line = f"- {sub_name}"
                if plan:
                    line += f" [{plan}]"
                if cost:
                    line += f" {cost:,.0f}원/월"
                if payment_date:
                    line += f" (결제일: {payment_date})"
                if status:
                    line += f" ({status})"
                lines.append(line)
            return "\n".join(lines)
        return "구독 서비스 정보가 없습니다."

    if name == "get_subscription_cost":
        subs = _query_subscriptions()
        if subs:
            monthly_total = 0
            active_count = 0
            for s in subs:
                cost = s.get("Monthly Fee", s.get("Cost", s.get("비용", 0))) or 0
                status = s.get("Status", s.get("상태", ""))
                if status.lower() not in ("cancelled", "해지", "중지"):
                    monthly_total += cost
                    active_count += 1
            lines = [
                "구독 비용 현황:",
                f"- 활성 구독: {active_count}개",
                f"- 월간 합계: {monthly_total:,.0f}원",
                f"- 연간 추정: {monthly_total * 12:,.0f}원"
            ]
            return "\n".join(lines)
        return "구독 정보가 없습니다."

    if name == "get_api_keys":
        kw = args.get("keyword")
        apis = _query_api_archive(kw)
        if apis:
            lines = [f"API/계정 정보 ({len(apis)}건):"]
            for a in apis:
                api_name = a.get("Entry name", a.get("Name", ""))
                key = a.get("API Key", a.get("Key", ""))
                status = a.get("Status", "")
                line = f"- {api_name}"
                if key:
                    masked = key[:8] + "..." if len(str(key)) > 8 else key
                    line += f" (Key: {masked})"
                if status:
                    line += f" [{status}]"
                lines.append(line)
            return "\n".join(lines)
        return "API 정보가 없습니다."

    return "알 수 없는 도구"


def handle(message, mode="chat", session=None, image_urls=None):
    if mode == "payment_reminder":
        subs = _query_subscriptions()
        today = datetime.now()
        reminders = []
        for s in subs:
            payment_date = s.get("Payment Date", s.get("결제일", ""))
            sub_name = s.get("Entry name", s.get("Name", ""))
            cost = s.get("Monthly Fee", s.get("Cost", s.get("비용", 0))) or 0
            if not payment_date:
                continue
            try:
                if isinstance(payment_date, str) and len(payment_date) >= 10:
                    pay_date = datetime.strptime(payment_date[:10], '%Y-%m-%d')
                    diff = (pay_date - today).days
                    if 0 <= diff <= 3:
                        reminders.append(f"{sub_name} 결제일 D-{diff} ({payment_date}) {cost:,.0f}원")
                elif isinstance(payment_date, (int, float)):
                    day = int(payment_date)
                    if today.day <= day <= today.day + 3:
                        reminders.append(f"{sub_name} 매월 {day}일 결제 {cost:,.0f}원")
            except Exception:
                continue
        if reminders:
            return {"response": "결제일 알림:\n" + "\n".join(reminders), "domain": DOMAIN}
        return {"response": "", "domain": DOMAIN}

    if not message:
        return {"error": "메시지가 필요합니다", "domain": DOMAIN}

    # Build context
    subs = _query_subscriptions()
    recent_tools = _query_tools("work_tool", limit=5)

    context = f"""## 주요 업무 도구
{json.dumps(recent_tools[:5], ensure_ascii=False, indent=1)}
## 구독 현황
{json.dumps(subs[:10], ensure_ascii=False, indent=1)}"""

    # Build messages from session history
    messages = []
    if session and session.get("messages"):
        messages = list(session["messages"][-16:])
    messages.append({"role": "user", "content": f"{context}\n\n## 사용자 요청\n{message}"})

    learned_rules = get_rules_as_prompt(DOMAIN)
    result = chat_with_tools_multi(
        SYSTEM_PROMPT + learned_rules, messages,
        TOOLS + [REQUEST_USER_CHOICE_TOOL, LEARN_RULE_TOOL], _exec_tool,
        domain=DOMAIN, image_urls=image_urls
    )

    output = {
        "response": result["response"],
        "domain": DOMAIN,
        "learning_events": result.get("learning_events", []),
    }
    if result.get("interactive"):
        output["interactive"] = result["interactive"]
    return output
