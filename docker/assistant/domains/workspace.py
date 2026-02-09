"""Workspace-wide Notion assistant domain.

Provides dynamic search/schema-aware CRUD over arbitrary Notion databases.
Acts as the universal AI agent for all Notion-backed queries.
"""

import json
from datetime import datetime, timedelta
from core.config import get_domain_config, get_all_aliases_map
from core.content_briefing import try_generate_monthly_briefing
from core.openai_client import (
    chat_completion,
    chat_with_tools_multi,
    REQUEST_USER_CHOICE_TOOL,
    LEARN_RULE_TOOL,
)
from core.memory import get_rules_as_prompt
from core.notion_client import (
    search_workspace,
    get_database_schema,
    retrieve_page,
    query_database,
    create_page,
    update_page,
    archive_page,
    append_blocks,
    parse_page_properties,
    build_properties_from_values,
    get_title_property_name,
)

DOMAIN = "workspace"

PLAIN_TEXT_RULE = "\n\n## 응답 규칙\n- 반드시 플레인 텍스트로 응답. 마크다운 문법은 사용하지 마세요.\n- 한국어로 간결하게 답변하세요."


def _build_db_catalog():
    """Build a DB catalog for the system prompt.

    Produces a lookup table: user-facing name -> database_id
    so the AI can directly resolve names like "디자인 페이지" to a DB ID.
    """
    all_aliases = get_all_aliases_map()

    # 1) Alias → DB ID direct mapping (primary lookup)
    lines = ["### 명칭 → database_id 매핑 (사용자가 이 이름을 쓰면 해당 DB 사용)"]
    seen_ids = set()
    for alias_name, info in all_aliases.items():
        lines.append(f"- \"{alias_name}\" → {info['db_id']}")
        seen_ids.add(info['db_id'])

    # 2) Add remaining DBs without aliases
    lines.append("\n### 기타 데이터베이스")
    for domain_name in ["schedule", "content", "finance", "travel", "tools", "business"]:
        cfg = get_domain_config(domain_name)
        dbs = cfg.get("databases", {})
        for db_key, db_id in dbs.items():
            if db_id and db_id not in seen_ids:
                lines.append(f"- [{domain_name}] {db_key}: {db_id}")
                seen_ids.add(db_id)

    return "\n".join(lines)


SYSTEM_PROMPT = """당신은 Notion을 속속들이 알고 있는 만능 AI 비서입니다.

## 핵심 역할
- 사용자의 모든 질문에 Notion 데이터를 기반으로 정확히 답변
- 일정, 구독, 도구, 콘텐츠, 재무, 여행 등 모든 영역 커버
- 정보가 바로 없으면 관련 DB를 찾아서 조회

## 중요: 시간대 (Timezone)
- 모든 시간은 한국 시간(KST, UTC+9) 기준입니다.
- 사용자가 "오전 10시"라고 하면 KST 10:00입니다.
- 절대로 UTC 변환하지 마세요. 사용자가 말한 시간을 그대로 사용하세요.
- 일정에 시간 포함 시: "YYYY-MM-DDT10:00:00+09:00" 형식 사용
- 예: "오전 10시" → "2026-02-08T10:00:00+09:00", "오후 3시" → "2026-02-08T15:00:00+09:00"

## 데이터베이스 명칭 매핑
사용자가 아래 명칭을 사용하면, 반드시 매핑된 database_id를 사용하세요.
예: "디자인 페이지에 기록해줘" → "디자인페이지" 매핑의 DB ID로 create_record 호출

{db_catalog}

## create_record 필수 규칙
- create_record 호출 시, values에 반드시 제목(title 속성)을 포함하세요.
- 각 DB마다 title 속성명이 다릅니다. 먼저 inspect_database로 확인하거나, 아래 매핑을 참조하세요.
- 예: 웍스 탭 → values: {{"Entry name": "주식 정보"}}
- 예: 일정 → values: {{"Entry name": "회의", "Date": "2026-02-09"}}
- 예: 재무 → values: {{"Entry": "커피", "Amount": 5000, "Type": "지출"}}
- values를 null이나 빈 객체로 보내지 마세요. 반드시 제목과 필요한 필드를 채우세요.

## 재무(지출/수입) 기록 방법
재무 Timeline DB (database_id는 DB 카탈로그 참조) 속성:
- Entry (title): 거래 내역명 (예: "시계 구매", "커피")
- Amount (number): 금액 (양수)
- Date (date): 거래일 (예: "2026-02-07")
- Type (select): "지출" 또는 "수입"
- Memo (rich_text): 메모
지출/수입 기록 시 create_record 사용. values 예시: {{"Entry": "시계 구매", "Amount": 10000000, "Date": "2026-02-07", "Type": "지출"}}

## 일정 조회/수정 방법
일정 DB (database_id는 DB 카탈로그 참조) 속성:
- Entry name (title): 일정 제목
- Date (date): 날짜/시간
- Completed (checkbox): 완료 여부
- Notes (rich_text): 메모
- Location (Entry) (rich_text): 장소

일정 검색 시:
1. 먼저 query_with_filter로 날짜 범위 필터링해서 후보를 가져옴
2. 제목으로 찾을 때 contains 필터 사용 (부분 일치: "아카데미" → "아카데미 이동" 매칭)
3. 결과에서 page_id를 사용해 update_record로 수정

일정 수정 예시:
1. query_with_filter로 해당 일정 검색 → page_id 확보
2. update_record(page_id=..., values={{"Date": "2026-02-08T10:00:00+09:00"}})

## 자주 쓰는 필터 패턴
- 특정 날짜 일정: {{"property": "Date", "date": {{"equals": "2026-02-04"}}}}
- 날짜 범위: {{"and": [{{"property": "Date", "date": {{"on_or_after": "2026-02-01"}}}}, {{"property": "Date", "date": {{"on_or_before": "2026-02-07"}}}}]}}
- 미완료 항목: {{"property": "Completed", "checkbox": {{"equals": false}}}}
- 활성 구독: {{"property": "Status", "status": {{"equals": "Subscribe"}}}}
- 제목 검색: {{"property": "Entry name", "title": {{"contains": "키워드"}}}}

## 사고 방식
1. 질문을 분석하여 어떤 DB가 필요한지 판단
2. 필요하면 query_with_filter로 정확한 필터를 적용해 조회
3. 결과가 없으면 search_workspace로 범위를 넓혀 검색
4. 찾은 데이터를 기반으로 명확하게 답변

## 페이지 본문 작성 (중요!)
사용자가 "본문에 기입", "본문에 내용 작성", "페이지에 내용 추가", "본문에 다음 내용 기입" 등을 요청하면:
1. create_record로 페이지를 먼저 생성 (또는 기존 페이지 page_id 확보)
2. append_blocks_to_page로 페이지 본문에 내용 추가 (page_id + content)
- Notes 속성에 쓰는 것이 아닙니다! 반드시 append_blocks_to_page 사용
- "등록하고 본문에 기입해줘" → create_record → append_blocks_to_page 2단계

## 키워드별 저장 대상 DB (중요!)
사용자가 아래 키워드를 사용하면 반드시 해당 DB에 저장:
- "뉴스탭에 ~해줘" → 뉴스탭 매핑 DB (news)에 create_record
- "롤탭에 ~해줘" / "웍스탭에 ~해줘" / "노트에 ~해줘" → works 매핑 DB에 create_record
- 키워드와 DB 매핑은 위 "데이터베이스 명칭 매핑" 섹션 참조

## 날짜 자동 기입
- create_record 시 date 타입 속성에 값을 지정하지 않으면 오늘 날짜가 자동으로 기입됩니다
- 사용자가 명시적으로 날짜를 지정한 경우에만 해당 날짜를 사용

## 콘텐츠 탭 브리핑/요약 (중요!)
사용자가 콘텐츠 탭별 브리핑이나 요약을 요청하면 해당 DB를 조회하여 요약 브리핑합니다.

콘텐츠 탭 → DB 매핑:
- 인사이트 / 인사이트탭 / 인사이트 페이지 → insights DB
- AI / AI탭 / 에이아이탭 → AI DB
- 디자인 / 디자인탭 → Design DB
- 브랜딩 / 브랜딩탭 → Branding DB
- 빌드 / 빌드탭 → Build DB
- 마케팅 / 마케팅탭 → Marketing DB

요청 예시와 처리 방법:
- "인사이트 탭 AI 관련 콘텐츠 요약해서 브리핑해줘" → insights DB에서 keyword="AI"로 summarize_records
- "이번주 브랜딩 관련 뉴스들 요약 브리핑해줘" → Branding DB에서 query_with_filter(날짜 필터) 후 결과를 요약
- "디자인 탭 최근 콘텐츠 브리핑해줘" → Design DB에서 summarize_records
- "마케팅 관련 인사이트 요약해줘" → Marketing DB 또는 insights DB에서 keyword="마케팅"으로 summarize_records

처리 흐름:
1. 요청에서 대상 탭(DB)과 키워드를 파악
2. 날짜 조건이 있으면 query_with_filter로 필터링, 없으면 summarize_records로 전체 요약
3. 특정 주제 키워드가 있으면 keyword 파라미터에 전달

## 작업 원칙
- "모르겠습니다" 대신 반드시 관련 DB를 조회해서 답변 시도
- 쓰기 작업(create/update/archive)은 반드시 도구를 호출하여 실행
- 결과에 page_id/database_id 포함하지 않아도 됨 (사용자에게 불필요)
- 중간 오류/내부 메시지는 사용자에게 보여주지 말고, 최종 결과만 자연스럽게 전달
- "[내부 지시]"로 시작하는 메시지는 시스템 안내이므로 사용자에게 절대 노출하지 마세요""" + PLAIN_TEXT_RULE

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_workspace",
            "description": "워크스페이스 전체에서 페이지/데이터베이스 검색",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "검색어"},
                    "object_type": {
                        "type": "string",
                        "description": "page|database|page_or_database",
                        "enum": ["page", "database", "page_or_database"],
                    },
                    "limit": {"type": "integer", "description": "최대 결과 수"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_database",
            "description": "데이터베이스 스키마(필드 구조) 조회",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "Notion database ID"}
                },
                "required": ["database_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_records",
            "description": "데이터베이스 레코드 조회 (키워드 검색)",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "Notion database ID"},
                    "keyword": {"type": "string", "description": "타이틀 검색 키워드"},
                    "limit": {"type": "integer", "description": "최대 결과 수"},
                },
                "required": ["database_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_with_filter",
            "description": "Notion 필터로 데이터베이스 조회. 날짜, 상태, 체크박스 등 고급 필터 지원",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string", "description": "Notion database ID"},
                    "filter": {
                        "type": "object",
                        "description": "Notion API 필터 객체. 예: {\"property\": \"Date\", \"date\": {\"equals\": \"2026-02-04\"}}",
                    },
                    "sorts": {
                        "type": "array",
                        "description": "정렬 배열. 예: [{\"property\": \"Date\", \"direction\": \"ascending\"}]",
                        "items": {
                            "type": "object",
                            "properties": {
                                "property": {"type": "string"},
                                "direction": {"type": "string", "enum": ["ascending", "descending"]}
                            },
                            "required": ["property", "direction"]
                        },
                    },
                    "limit": {"type": "integer", "description": "최대 결과 수 (기본 20)"},
                },
                "required": ["database_id", "filter"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_record",
            "description": "데이터베이스에 새 레코드 생성. 반드시 values에 제목(title 속성)을 포함해야 합니다. DB 스키마의 title 속성명을 키로 사용하세요.",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string"},
                    "values": {
                        "type": "object",
                        "description": "키=속성명, 값=입력값. 반드시 title 속성 포함. 예: {\"Entry name\":\"주식 정보\",\"Memo\":\"메모 내용\"}",
                    },
                },
                "required": ["database_id", "values"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_record",
            "description": "기존 레코드의 필드 수정",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                    "values": {"type": "object"},
                },
                "required": ["page_id", "values"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "archive_record",
            "description": "레코드 보관(아카이브)",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string"},
                },
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_records",
            "description": "조회한 레코드를 요약 브리핑",
            "parameters": {
                "type": "object",
                "properties": {
                    "database_id": {"type": "string"},
                    "keyword": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["database_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "append_blocks_to_page",
            "description": "페이지 본문(body)에 텍스트 블록을 추가. '본문에 기입', '페이지에 내용 작성' 등의 요청에 사용. Notes 속성이 아닌 페이지 본문에 씁니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "string", "description": "대상 페이지 ID"},
                    "content": {"type": "string", "description": "본문에 추가할 텍스트 내용"},
                },
                "required": ["page_id", "content"],
            },
        },
    },
]


def _parse_values(values):
    if isinstance(values, dict):
        return values
    if isinstance(values, str):
        try:
            parsed = json.loads(values)
            if isinstance(parsed, dict):
                return parsed
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _format_search_results(results, limit):
    lines = [f"검색 결과: {len(results[:limit])}건"]
    for item in results[:limit]:
        obj = item.get("object", "")
        title = ""
        if obj == "database":
            title = "".join(t.get("plain_text", "") for t in item.get("title", []))
            dbid = item.get("id", "")
            lines.append(f"- [DB] {title or '(제목 없음)'} (database_id: {dbid})")
        else:
            props = item.get("properties", {})
            for _, pv in props.items():
                if pv.get("type") == "title":
                    title = "".join(t.get("plain_text", "") for t in pv.get("title", []))
                    break
            pid = item.get("id", "")
            lines.append(f"- [PAGE] {title or '(제목 없음)'} (page_id: {pid})")
    return "\n".join(lines)


def _exec_tool(name, args):
    if name == "search_workspace":
        query = args.get("query", "")
        object_type = args.get("object_type", "page_or_database")
        limit = int(args.get("limit", 10) or 10)
        sr = search_workspace(query, object_type=object_type, page_size=min(limit, 100))
        if not sr.get("success"):
            return f"검색 실패: {sr.get('error', 'unknown error')}"
        return _format_search_results(sr.get("results", []), limit)

    if name == "inspect_database":
        database_id = args.get("database_id", "")
        schema_res = get_database_schema(database_id)
        if not schema_res.get("success"):
            return f"스키마 조회 실패: {schema_res.get('error', 'unknown error')}"

        schema = schema_res.get("schema", {})
        title_prop = get_title_property_name(schema)
        lines = [
            f"데이터베이스: {schema_res.get('title', '(제목 없음)')}",
            f"database_id: {database_id}",
            f"title_property: {title_prop or '(없음)'}",
            "속성:",
        ]
        for prop_name, prop_def in schema.items():
            lines.append(f"- {prop_name}: {prop_def.get('type', 'unknown')}")
        return "\n".join(lines)

    if name == "query_records":
        database_id = args.get("database_id", "")
        keyword = args.get("keyword", "")
        limit = int(args.get("limit", 10) or 10)

        schema_res = get_database_schema(database_id)
        if not schema_res.get("success"):
            return f"DB 스키마 조회 실패: {schema_res.get('error', 'unknown error')}"

        schema = schema_res.get("schema", {})
        filter_obj = None
        if keyword:
            title_prop = get_title_property_name(schema)
            if title_prop:
                filter_obj = {"property": title_prop, "title": {"contains": keyword}}

        qr = query_database(
            database_id,
            filter_obj=filter_obj,
            page_size=min(limit, 100),
            max_results=limit,
        )
        if not qr.get("success"):
            return f"레코드 조회 실패: {qr.get('error', 'unknown error')}"

        parsed = [parse_page_properties(p) for p in qr.get("results", [])]
        if not parsed:
            return "조회된 레코드가 없습니다."

        lines = [f"레코드 {len(parsed)}건"]
        for row in parsed:
            parts = []
            for key, val in row.items():
                if key == "id":
                    continue
                if val is None or val == "" or val == []:
                    continue
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                parts.append(f"{key}: {val}")
            lines.append("- " + " | ".join(parts))
        return "\n".join(lines)

    if name == "query_with_filter":
        database_id = args.get("database_id", "")
        filter_obj = args.get("filter")
        sorts = args.get("sorts")
        limit = int(args.get("limit", 20) or 20)

        if isinstance(filter_obj, str):
            try:
                filter_obj = json.loads(filter_obj)
            except (json.JSONDecodeError, TypeError):
                return "필터 JSON 파싱 실패. 올바른 Notion 필터 객체를 전달하세요."

        if isinstance(sorts, str):
            try:
                sorts = json.loads(sorts)
            except (json.JSONDecodeError, TypeError):
                sorts = None

        qr = query_database(
            database_id,
            filter_obj=filter_obj,
            sorts=sorts,
            page_size=min(limit, 100),
            max_results=limit,
        )
        if not qr.get("success"):
            return f"필터 조회 실패: {qr.get('error', 'unknown error')}"

        parsed = [parse_page_properties(p) for p in qr.get("results", [])]
        if not parsed:
            return "조건에 맞는 레코드가 없습니다."

        lines = [f"조회 결과: {len(parsed)}건"]
        for row in parsed:
            parts = []
            for key, val in row.items():
                if key == "id":
                    continue
                if val is None or val == "" or val == []:
                    continue
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                parts.append(f"{key}: {val}")
            lines.append("- " + " | ".join(parts))
        return "\n".join(lines)

    if name == "create_record":
        database_id = args.get("database_id", "")
        values = _parse_values(args.get("values"))

        # values가 비어있으면 → args의 다른 필드나 title 힌트에서 복구 시도
        if not values:
            title_hint = args.get("title") or args.get("name") or args.get("entry_name")
            if title_hint:
                values = {"title": str(title_hint)}
            else:
                return "[내부 지시] values가 비어있습니다. values에 제목을 포함해서 다시 호출하세요."

        schema_res = get_database_schema(database_id)
        if not schema_res.get("success"):
            return f"DB 스키마 조회 실패: {schema_res.get('error', 'unknown error')}"

        schema = schema_res.get("schema", {})
        title_prop = get_title_property_name(schema)

        # 날짜 자동 기입: date 속성이 있는데 값이 비어있으면 오늘 날짜 자동 추가
        today_str = datetime.now().strftime("%Y-%m-%d")
        for prop_name, prop_def in schema.items():
            if prop_def.get("type") == "date":
                norm_key = prop_name.strip().lower().replace(" ", "").replace("_", "")
                has_value = False
                for k, v in values.items():
                    if k.strip().lower().replace(" ", "").replace("_", "") == norm_key and v:
                        has_value = True
                        break
                if not has_value:
                    values[prop_name] = today_str

        properties = build_properties_from_values(schema, values)

        # title이 properties에 없으면 → values의 아무 문자열 값이라도 title로 사용
        if title_prop and title_prop not in properties:
            fallback_title = None
            # 1차: 알려진 키명에서 찾기
            for key in ("title", "name", "entry", "Entry name", "Entry",
                        "entry_name", "entry name", "제목"):
                if values.get(key):
                    fallback_title = values[key]
                    break
            # 2차: values의 첫 번째 문자열 값 사용
            if not fallback_title:
                for v in values.values():
                    if v and isinstance(v, str):
                        fallback_title = v
                        break
            if fallback_title:
                properties[title_prop] = {"title": [{"text": {"content": str(fallback_title)}}]}

        if not properties:
            return "[내부 지시] 생성할 필드 값이 없습니다. values에 제목을 포함해서 다시 호출하세요."

        cr = create_page(database_id, properties)
        if not cr.get("success"):
            return f"레코드 생성 실패: {cr.get('error', 'unknown error')}"

        created = cr.get("data", {})
        return f"생성 완료 (page_id: {created.get('id', '')})"

    if name == "update_record":
        page_id = args.get("page_id", "")
        values = _parse_values(args.get("values"))

        page_res = retrieve_page(page_id)
        if not page_res.get("success"):
            return f"페이지 조회 실패: {page_res.get('error', 'unknown error')}"

        page = page_res.get("page", {})
        parent = page.get("parent", {})
        database_id = parent.get("database_id", "")
        if not database_id:
            return "해당 페이지는 데이터베이스 기반 레코드가 아닙니다."

        schema_res = get_database_schema(database_id)
        if not schema_res.get("success"):
            return f"DB 스키마 조회 실패: {schema_res.get('error', 'unknown error')}"

        schema = schema_res.get("schema", {})
        properties = build_properties_from_values(schema, values)
        if not properties:
            return "수정할 필드 값이 없습니다. values를 확인하세요."

        ur = update_page(page_id, properties)
        if not ur.get("success"):
            return f"레코드 수정 실패: {ur.get('error', 'unknown error')}"
        return f"수정 완료 (page_id: {page_id})"

    if name == "archive_record":
        page_id = args.get("page_id", "")
        ar = archive_page(page_id)
        if not ar.get("success"):
            return f"보관 실패: {ar.get('error', 'unknown error')}"
        return f"보관 완료 (page_id: {page_id})"

    if name == "summarize_records":
        database_id = args.get("database_id", "")
        keyword = args.get("keyword", "")
        limit = int(args.get("limit", 20) or 20)

        schema_res = get_database_schema(database_id)
        if not schema_res.get("success"):
            return f"DB 스키마 조회 실패: {schema_res.get('error', 'unknown error')}"

        schema = schema_res.get("schema", {})
        filter_obj = None
        if keyword:
            title_prop = get_title_property_name(schema)
            if title_prop:
                filter_obj = {"property": title_prop, "title": {"contains": keyword}}

        qr = query_database(database_id, filter_obj=filter_obj, page_size=min(limit, 100), max_results=limit)
        if not qr.get("success"):
            return f"레코드 조회 실패: {qr.get('error', 'unknown error')}"

        parsed = [parse_page_properties(p) for p in qr.get("results", [])]
        if not parsed:
            return "요약할 데이터가 없습니다."

        content = json.dumps(parsed, ensure_ascii=False)
        summary = chat_completion(
            [
                {"role": "system", "content": "당신은 Notion 데이터 요약 비서입니다. 핵심만 한국어로 짧게 요약하세요."},
                {"role": "user", "content": content},
            ],
            max_tokens=800,
            temperature=0.2,
        )
        return summary or "요약 결과가 없습니다."

    if name == "append_blocks_to_page":
        page_id = args.get("page_id", "")
        content = args.get("content", "")
        if not content:
            return "추가할 내용이 없습니다."

        # 줄바꿈 기준으로 paragraph 블록 생성
        blocks = []
        for line in content.split("\n"):
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": line}}]
                },
            })

        result = append_blocks(page_id, blocks)
        if not result.get("success"):
            return f"본문 추가 실패: {result.get('error', 'unknown error')}"
        return f"페이지 본문에 내용을 추가했습니다."

    return "알 수 없는 도구"


def handle(message, mode="chat", session=None, image_urls=None):
    if not message:
        return {"error": "메시지가 필요합니다", "domain": DOMAIN}

    # 콘텐츠 탭 월간 브리핑 요청은 결정적으로 처리 (LLM 도구 선택 불확실성 제거)
    if mode == "chat":
        briefing = try_generate_monthly_briefing(message)
        if briefing:
            return {"response": briefing, "domain": DOMAIN}

    messages = []
    if session and session.get("messages"):
        messages = list(session["messages"][-16:])

    # DB 카탈로그와 현재 날짜를 시스템 프롬프트에 주입
    now = datetime.now()
    db_catalog = _build_db_catalog()
    date_context = (
        f"\n\n## 현재 시각 정보\n"
        f"- 현재: {now.strftime('%Y-%m-%d %H:%M')} ({['월','화','수','목','금','토','일'][now.weekday()]}요일)\n"
        f"- 이번 주: {(now - timedelta(days=now.weekday())).strftime('%Y-%m-%d')} ~ "
        f"{(now + timedelta(days=6 - now.weekday())).strftime('%Y-%m-%d')}"
    )
    system_prompt = SYSTEM_PROMPT.format(db_catalog=db_catalog) + date_context

    messages.append({"role": "user", "content": message})

    learned_rules = get_rules_as_prompt(DOMAIN)

    # 같은 요청 안에서 동일 DB에 대한 create_record 중복 호출 방지
    created_pages = {}  # {database_id: page_id}

    def _extract_title_from_message(msg):
        """메시지에서 따옴표로 감싼 제목을 추출. 예: '훅', "김" → 훅, 김"""
        import re
        m = re.search(r"['\u2018\u2019\u201c\u201d\"](.*?)['\u2018\u2019\u201c\u201d\"]", msg)
        return m.group(1) if m else None

    def _exec_tool_guarded(name, args):
        if name == "create_record":
            db_id = args.get("database_id", "")
            if db_id in created_pages:
                return (f"성공: 이미 생성된 레코드를 사용하세요. page_id: {created_pages[db_id]}. "
                        f"create_record를 다시 호출하지 마세요. "
                        f"본문 작성이 필요하면 append_blocks_to_page(page_id=\"{created_pages[db_id]}\", content=\"...\")를 호출하세요.")
            # values가 비어있으면 원본 메시지에서 제목을 자동 추출하여 보정
            values = args.get("values")
            if not values or (isinstance(values, dict) and not values) or values == "null":
                title = _extract_title_from_message(message)
                if title:
                    args["values"] = {"Entry name": title}
            result = _exec_tool(name, args)
            if "생성 완료 (page_id:" in result:
                page_id = result.split("page_id: ")[1].rstrip(")")
                created_pages[db_id] = page_id
            return result
        return _exec_tool(name, args)

    # 명령형 요청(만들어줘, 기입해줘, 추가해줘 등)이면 도구 호출을 강제
    command_keywords = ["만들", "기입", "추가", "생성", "등록", "수정", "삭제", "기록", "작성", "저장"]
    is_command = any(kw in message for kw in command_keywords)

    result = chat_with_tools_multi(
        system_prompt + learned_rules,
        messages,
        TOOLS + [REQUEST_USER_CHOICE_TOOL, LEARN_RULE_TOOL],
        _exec_tool_guarded,
        max_tool_rounds=7,
        domain=DOMAIN,
        image_urls=image_urls,
        force_tool_call=is_command,
    )

    response_text = result.get("response", "")

    # 내부 에러 메시지가 사용자에게 노출되지 않도록 코드 레벨에서 차단
    error_patterns = ["[내부 지시]", "title 속성명", "스키마 에러",
                      "values가 비어", "제목이 없습니다",
                      "\"Entry name\"이 누락"]
    if any(pat in response_text for pat in error_patterns):
        if created_pages:
            response_text = "요청을 처리했습니다."
        else:
            response_text = "요청을 처리하지 못했습니다. 다시 시도해주세요."

    output = {
        "response": response_text,
        "domain": DOMAIN,
        "learning_events": result.get("learning_events", []),
    }
    if result.get("interactive"):
        output["interactive"] = result["interactive"]
    return output
