"""Finance domain handler — 재무 관리"""
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

DOMAIN = "finance"

PLAIN_TEXT_RULE = "\n\n## 응답 규칙\n- 반드시 플레인 텍스트로 응답. **bold**, [link](url), # heading, `code` 등 마크다운 절대 금지.\n- 이모지 사용 가능."


def _cfg():
    return get_domain_config(DOMAIN)


def _db(key):
    return _cfg().get("databases", {}).get(key, "")


SYSTEM_PROMPT = """당신은 재무 관리 비서입니다. 계좌, 지출, 예산을 관리합니다.

## 역할
- 잔액/지출/수입 조회
- 거래 기록 추가/수정/삭제
- 카테고리별 분석, 월간 리포트
- 예산 대비 현황

## 중요: 한국어 금액 변환 규칙
사용자가 한국어로 금액을 말하면 반드시 정확히 숫자로 변환하세요:
- "천원" = 1,000원
- "만원" = 10,000원
- "십만원" = 100,000원
- "백만원" = 1,000,000원
- "천만원" = 10,000,000원
- "억" = 100,000,000원
- 조합: "3천원" = 3,000원, "5만원" = 50,000원, "천만원짜리" = 10,000,000원
- 예시: "커피 5천원" → amount: 5000, "시계 천만원" → amount: 10000000, "월급 삼백만원" → amount: 3000000

## 거래 추가 — 빠르게 기록하는 것이 최우선
- 사용자가 지출/수입을 말하면 즉시 기록하세요. 질문하지 마세요.
- when: 언급 없으면 자동으로 이번 달 설정 (예: "2026년 02월")
- account: 언급 없으면 자동으로 "토스뱅크" 설정 (기본 계좌)
- type: 기본값 "지출". "월급", "수입", "벌었" 등이 있으면 "수입"
- 카테고리나 계좌를 물어보지 마세요. 추론해서 바로 기록하세요.
- 사용자가 구체적으로 수정을 요청할 때만 변경하세요.

## 카테고리 매핑 (실제 DB 항목명 그대로 사용)
지출 카테고리:
- 밥/음식/배달/외식 → "식비"
- 커피/카페/간식/음료/디저트 → "카페 | 간식"
- 택시/버스/지하철/주유/주차/톨게이트 → "교통비"
- 옷/신발/시계/화장품/미용실/헤어 → "의복 | 미용"
- 월세/관리비/인터넷/통신/핸드폰 → "관리 | 통신"
- 병원/약/헬스/건강 → "의료 | 건강"
- 영화/공연/게임/취미/운동 → "문화 | 여가"
- 호텔/항공/여행/숙박 → "여행 | 숙박"
- 학원/강의/책/교육 → "교육"
- 생필품/마트/생활용품/세탁 → "생활비"
- 선물/선물비 → "선물"
- 축의금/조의금/부조금 → "경조사"
- 대출/이자 → "대출금"
- 세금/국민연금/건강보험 → "세금"
- 임대료/사무실 → "임대료"
- 용돈/부모님 → "용돈"
- 이체/송금 → "송금"
- 그 외 지출 → "기타지출"
수입 카테고리:
- 월급/급여 → "급여소득"
- 프리랜서/외주/사업 → "사업소득"
- 그 외 수입 → "기타소득"
구독 카테고리 (자동 결제):
- ChatGPT → "ChatGPT", Claude → "Claude", Notion → "Notion"
- Figma → "Figma", YouTube → "YouTube", Gemini → "Gemini"
- 넷플릭스/Netflix → "넷플릭스", iCloud → "iCloud"

## 거래 수정/삭제 절차
- 사용자가 거래 삭제나 수정을 요청하면, 먼저 get_transactions로 해당 거래를 조회하여 page_id를 확인하세요.
- 조회 결과의 (id:xxx) 부분이 page_id입니다.
- 확인된 page_id로 delete_transaction 또는 update_transaction을 실행하세요.
- 사용자가 "진행해", "삭제해" 등으로 동의하면 즉시 실행하세요. 학습만 하고 끝내지 마세요.

## 응답 스타일
- 한국어, 금액은 원 단위로, 간결하게""" + PLAIN_TEXT_RULE

TOOLS = [
    {"type": "function", "function": {
        "name": "get_accounts",
        "description": "계좌 목록 및 잔액 조회",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "add_transaction",
        "description": "지출/수입 거래 기록 추가. when과 account도 함께 설정하세요.",
        "parameters": {"type": "object", "properties": {
            "entry": {"type": "string", "description": "거래 내용"},
            "amount": {"type": "number", "description": "금액"},
            "category": {"type": "string", "description": "카테고리 (식비, 교통, 쇼핑 등)"},
            "type": {"type": "string", "description": "수입 또는 지출"},
            "when": {"type": "string", "description": "월 기간 (예: '2026년 02월'). 이번 달이면 현재 월로 설정."},
            "account": {"type": "string", "description": "계좌 (토스뱅크, 카카오뱅크, 하나은행, 신한은행)"},
            "memo": {"type": "string"}
        }, "required": ["entry", "amount"]}
    }},
    {"type": "function", "function": {
        "name": "get_transactions",
        "description": "거래 내역 조회 (기간/키워드)",
        "parameters": {"type": "object", "properties": {
            "keyword": {"type": "string"},
            "start_date": {"type": "string", "description": "YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD"}
        }}
    }},
    {"type": "function", "function": {
        "name": "get_categories",
        "description": "카테고리별 예산/지출 현황",
        "parameters": {"type": "object", "properties": {}}
    }},
    {"type": "function", "function": {
        "name": "delete_transaction",
        "description": "거래 기록 삭제 (Notion 페이지 아카이브). 삭제 전 반드시 get_transactions로 page_id를 확인하세요.",
        "parameters": {"type": "object", "properties": {
            "page_id": {"type": "string", "description": "삭제할 Notion 페이지 ID"},
            "reason": {"type": "string", "description": "삭제 사유"}
        }, "required": ["page_id"]}
    }},
    {"type": "function", "function": {
        "name": "update_transaction",
        "description": "기존 거래 기록 수정 (카테고리, 금액, when, account 등). 수정 전 반드시 get_transactions로 page_id를 확인하세요.",
        "parameters": {"type": "object", "properties": {
            "page_id": {"type": "string", "description": "수정할 Notion 페이지 ID"},
            "entry": {"type": "string", "description": "거래 내용 (변경 시)"},
            "amount": {"type": "number", "description": "금액 (변경 시)"},
            "category": {"type": "string", "description": "카테고리 (변경 시)"},
            "type": {"type": "string", "description": "수입/지출 (변경 시)"},
            "when": {"type": "string", "description": "월 기간 (예: '2026년 02월') (변경 시)"},
            "account": {"type": "string", "description": "계좌 (토스뱅크, 카카오뱅크, 하나은행, 신한은행) (변경 시)"},
            "memo": {"type": "string", "description": "메모 (변경 시)"}
        }, "required": ["page_id"]}
    }}
]


def _query_accounts():
    r = query_database(_db("accounts"))
    if isinstance(r, dict):
        return [parse_page_properties(p) for p in r.get("results", [])]
    return r


def _query_transactions(keyword=None, start=None, end=None, limit=20, resolve_rels=False):
    filters = []
    if keyword:
        filters.append({"property": "Entry", "title": {"contains": keyword}})
    if start:
        filters.append({"property": "\x08Date", "date": {"on_or_after": start}})
    if end:
        filters.append({"property": "\x08Date", "date": {"on_or_before": end}})
    filt = {"and": filters} if len(filters) > 1 else (filters[0] if filters else None)
    r = query_database(_db("timeline"), filter_obj=filt,
                       sorts=[{"property": "\x08Date", "direction": "descending"}],
                       page_size=limit)
    if isinstance(r, dict):
        return [parse_page_properties(p, resolve_rels=resolve_rels) for p in r.get("results", [])]
    return r


def _query_categories():
    r = query_database(_db("categories"))
    if isinstance(r, dict):
        return [parse_page_properties(p) for p in r.get("results", [])]
    return r


# Category name → page_id cache (populated on first lookup)
_category_cache = {}

# When (month) name → page_id cache  (e.g. "2026년 02월" → page_id)
_when_cache = {}

# Account name → page_id cache  (e.g. "토스뱅크" → page_id)
_account_cache = {}


def _find_category_id(category_name):
    """Find the Notion page ID for a category name.

    Queries the categories DB once and caches results. Falls back to
    partial matching if exact match fails.
    """
    if not _category_cache:
        cats = _query_categories()
        if isinstance(cats, list):
            for c in cats:
                name = c.get("항목", "")
                if name:
                    _category_cache[name] = c["id"]

    # Exact match
    if category_name in _category_cache:
        return _category_cache[category_name]

    # Partial match (e.g. "식비" in "식비", "교통" in "교통비")
    for cached_name, page_id in _category_cache.items():
        if category_name in cached_name or cached_name in category_name:
            return page_id

    return None


def _find_when_id(when_name):
    """Find the Notion page ID for a month period name.

    Queries the monthly DB once and caches. Supports partial matching
    (e.g. "2월" matches "2026년 2월", "02월" matches "2월").
    """
    if not _when_cache:
        r = query_database(_db("monthly"), page_size=50)
        if isinstance(r, dict):
            for p in r.get("results", []):
                parsed = parse_page_properties(p)
                # Monthly DB title property is "일자" (e.g. "2026년 2월")
                name = parsed.get("일자", "")
                if name:
                    _when_cache[name] = parsed["id"]

    if not when_name:
        return None

    # Build variants: "2026년 02월" ↔ "2026년 2월"
    import re
    no_pad = re.sub(r'(\d+)년\s*0?(\d+)월', r'\1년 \2월', when_name)
    m = re.match(r'(\d+)년\s*(\d+)월', when_name)
    zero_pad = f"{m.group(1)}년 {int(m.group(2)):02d}월" if m else when_name
    variants = {when_name, no_pad, zero_pad}

    # Exact match (try all variants)
    for v in variants:
        if v in _when_cache:
            return _when_cache[v]

    # Partial match
    for cached_name, page_id in _when_cache.items():
        for v in variants:
            if v in cached_name or cached_name in v:
                return page_id

    return None


def _find_account_id(account_name):
    """Find the Notion page ID for an account name.

    Queries the accounts DB once and caches. Supports partial matching.
    """
    if not _account_cache:
        accs = _query_accounts()
        if isinstance(accs, list):
            for a in accs:
                name = a.get("Bank", a.get("이름", ""))
                if name:
                    _account_cache[name] = a["id"]

    # Exact match
    if account_name in _account_cache:
        return _account_cache[account_name]

    # Partial match (e.g. "토스" matches "토스뱅크")
    for cached_name, page_id in _account_cache.items():
        if account_name in cached_name or cached_name in account_name:
            return page_id

    return None


def _exec_tool(name, args):
    if name == "get_accounts":
        accs = _query_accounts()
        if accs:
            lines = ["계좌 현황:"]
            for a in accs:
                bank = a.get("Bank", a.get("이름", ""))
                bal = a.get("잔액", a.get("Current Balance", 0))
                lines.append(f"- {bank}: {bal:,.0f}원" if bal else f"- {bank}")
            return "\n".join(lines)
        return "계좌 정보가 없습니다."

    if name == "add_transaction":
        entry = args.get("entry", "지출")
        amount = args.get("amount", 0)
        props = {
            "Entry": {"title": [{"text": {"content": entry}}]},
            "Amount": {"number": amount},
            "\x08Date": {"date": {"start": datetime.now().strftime('%Y-%m-%d')}}
        }
        if args.get("category"):
            cat_id = _find_category_id(args["category"])
            if cat_id:
                props["Category"] = {"relation": [{"id": cat_id}]}
        if args.get("type"):
            props["Type"] = {"select": {"name": args["type"]}}
        # When: 월 + 해당 연도 전체 항상 포함
        when_rels = []
        if args.get("when"):
            when_id = _find_when_id(args["when"])
            if when_id:
                when_rels.append({"id": when_id})
        yearly_name = f"{datetime.now().year}년 전체"
        yearly_id = _find_when_id(yearly_name)
        if yearly_id and not any(r["id"] == yearly_id for r in when_rels):
            when_rels.append({"id": yearly_id})
        if when_rels:
            props["When"] = {"relation": when_rels}
        if args.get("account"):
            acc_id = _find_account_id(args["account"])
            if acc_id:
                props["Account"] = {"relation": [{"id": acc_id}]}
        if args.get("memo"):
            props["Memo"] = {"rich_text": [{"text": {"content": args["memo"]}}]}

        r = create_page(_db("timeline"), props)

        if not r["success"]:
            error_msg = r.get('error', '알 수 없는 오류')
            return f"거래 기록 실패: {error_msg}"

        extras = []
        if args.get("when"):
            extras.append(args["when"])
        if args.get("account"):
            extras.append(args["account"])
        extra_str = f" ({', '.join(extras)})" if extras else ""
        return f"거래 기록 완료! {entry} {amount:,.0f}원{extra_str}"

    if name == "get_transactions":
        txns = _query_transactions(args.get("keyword"), args.get("start_date"), args.get("end_date"))
        if txns:
            # Resolve names from local caches (no extra API calls)
            _rev_cat = {v: k for k, v in _category_cache.items()}
            _rev_when = {v: k for k, v in _when_cache.items()}
            _rev_acc = {v: k for k, v in _account_cache.items()}
            lines = [f"거래 내역 ({len(txns)}건):"]
            total = 0
            for t in txns[:15]:
                entry = t.get("Entry", "")
                amt = t.get("Amount", 0) or 0
                cat_ids = t.get("Category", [])
                if isinstance(cat_ids, list) and cat_ids:
                    cat = ", ".join(_rev_cat.get(cid, cid) for cid in cat_ids)
                else:
                    cat = str(cat_ids)
                when_ids = t.get("When", [])
                if isinstance(when_ids, list) and when_ids:
                    when = ", ".join(_rev_when.get(wid, "미설정") for wid in when_ids)
                else:
                    when = "미설정"
                acc_ids = t.get("Account", [])
                if isinstance(acc_ids, list) and acc_ids:
                    acc = ", ".join(_rev_acc.get(aid, "미설정") for aid in acc_ids)
                else:
                    acc = "미설정"
                date = t.get("\x08Date", {})
                date_str = date.get("start", "") if isinstance(date, dict) else ""
                pid = t.get("id", "")
                total += amt
                lines.append(f"- {entry}: {amt:,.0f}원 [{cat}] {date_str} when={when} account={acc} (id:{pid})")
            lines.append(f"\n합계: {total:,.0f}원")
            return "\n".join(lines)
        return "거래 내역이 없습니다."

    if name == "get_categories":
        cats = _query_categories()
        if cats:
            lines = ["카테고리별 현황:"]
            for c in cats:
                name_ = c.get("항목", "")
                budget = c.get("한 달 예산", 0) or 0
                spent = c.get("이번 달 지출", 0) or 0
                lines.append(f"- {name_}: 지출 {spent:,.0f}원 / 예산 {budget:,.0f}원")
            return "\n".join(lines)
        return "카테고리 정보가 없습니다."

    if name == "delete_transaction":
        page_id = args.get("page_id", "")
        if not page_id:
            return "삭제할 page_id가 필요합니다."
        r = archive_page(page_id)
        reason = args.get("reason", "")
        if r.get("success"):
            return f"거래 삭제 완료!{' (' + reason + ')' if reason else ''}"
        return f"삭제 실패: {r.get('error', '')}"

    if name == "update_transaction":
        page_id = args.get("page_id", "")
        if not page_id:
            return "수정할 page_id가 필요합니다."
        props = {}
        if "entry" in args:
            props["Entry"] = {"title": [{"text": {"content": args["entry"]}}]}
        if "amount" in args:
            props["Amount"] = {"number": args["amount"]}
        if "category" in args:
            cat_id = _find_category_id(args["category"])
            if cat_id:
                props["Category"] = {"relation": [{"id": cat_id}]}
        if "type" in args:
            props["Type"] = {"select": {"name": args["type"]}}
        if "when" in args:
            when_rels = []
            when_id = _find_when_id(args["when"])
            if when_id:
                when_rels.append({"id": when_id})
            yearly_name = f"{datetime.now().year}년 전체"
            yearly_id = _find_when_id(yearly_name)
            if yearly_id and not any(r["id"] == yearly_id for r in when_rels):
                when_rels.append({"id": yearly_id})
            if when_rels:
                props["When"] = {"relation": when_rels}
        if "account" in args:
            acc_id = _find_account_id(args["account"])
            if acc_id:
                props["Account"] = {"relation": [{"id": acc_id}]}
        if "memo" in args:
            props["Memo"] = {"rich_text": [{"text": {"content": args["memo"]}}]}
        if not props:
            return "수정할 내용이 없습니다."
        r = update_page(page_id, props)
        if r.get("success"):
            changes = ", ".join(k for k in props.keys())
            return f"거래 수정 완료! (변경: {changes})"
        return f"수정 실패: {r.get('error', '')}"

    return "알 수 없는 도구"


def handle(message, mode="chat", session=None, image_urls=None):
    if mode == "monthly_report":
        accs = _query_accounts()
        cats = _query_categories()
        now = datetime.now()
        first = now.replace(day=1).strftime('%Y-%m-%d')
        txns = _query_transactions(start=first, end=now.strftime('%Y-%m-%d'))
        prompt = "월간 재무 리포트 생성. 계좌 잔액, 카테고리별 지출, 총 지출/수입 요약. 이모지 사용. 한국어."
        content = f"계좌: {json.dumps(accs[:5], ensure_ascii=False)}\n카테고리: {json.dumps(cats[:10], ensure_ascii=False)}\n이번 달 거래: {json.dumps(txns[:20], ensure_ascii=False)}"
        resp = chat_completion([{"role": "system", "content": prompt}, {"role": "user", "content": content}], max_tokens=800)
        return {"response": resp, "domain": DOMAIN}

    if mode == "weekly_expense":
        now = datetime.now()
        week_start = (now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')
        txns = _query_transactions(start=week_start, end=now.strftime('%Y-%m-%d'))
        total = sum((t.get("Amount", 0) or 0) for t in txns)
        resp = f"이번 주 지출: {total:,.0f}원 ({len(txns)}건)"
        return {"response": resp, "domain": DOMAIN}

    if not message:
        return {"error": "메시지가 필요합니다", "domain": DOMAIN}

    # Build context — resolve category names locally (no extra API calls)
    accs = _query_accounts()
    now = datetime.now()
    recent_txns = _query_transactions(start=(now - timedelta(days=7)).strftime('%Y-%m-%d'), limit=10)

    # Pre-load all relation caches once (single query each)
    if not _category_cache:
        _find_category_id("")  # triggers _query_categories() + cache build
    if not _when_cache:
        _find_when_id("")  # triggers monthly DB query + cache build
    if not _account_cache:
        _find_account_id("")  # triggers accounts DB query + cache build

    # Build reverse maps: page_id → name
    _rev_cat = {v: k for k, v in _category_cache.items()}
    _rev_when = {v: k for k, v in _when_cache.items()}
    _rev_acc = {v: k for k, v in _account_cache.items()}

    # Enrich transactions with resolved names for context
    enriched_txns = []
    for t in recent_txns[:10]:
        t_copy = dict(t)
        cat_ids = t_copy.get("Category", [])
        if isinstance(cat_ids, list) and cat_ids:
            t_copy["Category"] = [_rev_cat.get(cid, cid) for cid in cat_ids]
        when_ids = t_copy.get("When", [])
        if isinstance(when_ids, list) and when_ids:
            t_copy["When"] = [_rev_when.get(wid, wid) for wid in when_ids]
        acc_ids = t_copy.get("Account", [])
        if isinstance(acc_ids, list) and acc_ids:
            t_copy["Account"] = [_rev_acc.get(aid, aid) for aid in acc_ids]
        enriched_txns.append(t_copy)

    context = f"""## 계좌 현황
{json.dumps(accs[:5], ensure_ascii=False, indent=1)}
## 최근 7일 거래
{json.dumps(enriched_txns, ensure_ascii=False, indent=1)}"""

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
