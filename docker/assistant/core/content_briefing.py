"""Monthly briefing generator for Beyondworks content tabs.

This module is used to generate "YYYY년 M월 <탭> 브리핑" responses from
Notion databases configured in config.json (domain: content).

Design goals:
- Deterministic DB/tab + month resolution (no LLM guessing).
- Only triggers for explicit "요약/브리핑/정리" requests mentioning a content tab.
- Uses the existing Notion + AI provider clients (stdlib-only).
"""

from __future__ import annotations

import re
from datetime import date, datetime

from .config import get_domain_config
from .notion_client import parse_page_properties, query_database
from .openai_client import chat_completion


_TAB_LABELS = {
    "AI": "AI",
    "Design": "디자인",
    "Branding": "브랜딩",
    "Build": "빌드",
    "Marketing": "마케팅",
    "insights": "인사이트",
    "news": "뉴스/팁",
    "scrap": "스크랩",
}

_TAB_PRIORITY = {
    "AI": 0,
    "Design": 1,
    "Branding": 2,
    "Build": 3,
    "Marketing": 4,
    "insights": 5,
    "news": 6,
    "scrap": 7,
}


def _norm(text: str) -> str:
    return re.sub(r"\s+", "", (text or "").lower())


def _looks_like_briefing_request(message_norm: str) -> bool:
    if not message_norm:
        return False

    if "브리핑" in message_norm:
        return True

    # "요약/정리"만 있는 문장은 범용 요청일 수 있어, 콘텐츠 문맥 단어가 같이 있을 때만 트리거
    if ("요약" in message_norm or "정리" in message_norm) and any(
        k in message_norm for k in ("탭", "페이지", "콘텐츠", "인사이트", "저장")
    ):
        return True

    return False


def _resolve_content_db_key(message_norm: str) -> str | None:
    cfg = get_domain_config("content")
    aliases = cfg.get("aliases", {}) or {}

    hits: list[tuple[int, int, str]] = []
    for alias, db_key in aliases.items():
        alias_norm = _norm(alias)
        if not alias_norm:
            continue
        if alias_norm in message_norm:
            prio = _TAB_PRIORITY.get(db_key, 999)
            hits.append((prio, -len(alias_norm), db_key))

    if not hits:
        return None

    hits.sort()
    return hits[0][2]


def _parse_year_month(message: str, now: datetime) -> tuple[int, int] | None:
    """Parse a year-month from the message.

    Supported:
    - "2026년 2월"
    - "2026-02" / "2026/02" / "2026.02"
    - "이번 달", "지난 달"
    - "2월" (year inferred as the most recent matching month)
    """
    text = message or ""

    # Explicit year/month (Korean)
    m = re.search(r"(20\d{2})\s*년\s*(\d{1,2})\s*월", text)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2))
        if 1 <= mo <= 12:
            return y, mo

    # Explicit year-month (numeric)
    m = re.search(r"(20\d{2})\s*[-/.]\s*(\d{1,2})", text)
    if m:
        y = int(m.group(1))
        mo = int(m.group(2))
        if 1 <= mo <= 12:
            return y, mo

    # Relative month keywords
    if re.search(r"이번\s*달", text):
        return now.year, now.month

    if re.search(r"(지난|저번)\s*달", text):
        y, mo = now.year, now.month - 1
        if mo == 0:
            return y - 1, 12
        return y, mo

    # Month only (infer year)
    m = re.search(r"(\d{1,2})\s*월", text)
    if m:
        mo = int(m.group(1))
        if 1 <= mo <= 12:
            # "2월"처럼 연도가 없으면, '가장 최근의 해당 월'로 해석
            y = now.year
            if mo > now.month:
                y -= 1
            return y, mo

    return None


def _month_range_iso(year: int, month: int) -> tuple[str, str]:
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    return start.isoformat(), end.isoformat()


def _build_date_filter(db_key: str, start_iso: str, end_iso: str) -> dict:
    """Build Notion filter object for the given DB key.

    Most content tabs use a date property named "Date" (type: date).
    Insights DB uses "Date" as created_time.
    """
    if db_key == "insights":
        return {
            "and": [
                {"property": "Date", "created_time": {"on_or_after": start_iso}},
                {"property": "Date", "created_time": {"before": end_iso}},
            ]
        }
    return {
        "and": [
            {"property": "Date", "date": {"on_or_after": start_iso}},
            {"property": "Date", "date": {"before": end_iso}},
        ]
    }


def _extract_items(rows: list[dict], max_summary_chars: int = 600) -> list[dict]:
    items: list[dict] = []
    for r in rows:
        title = r.get("Entry name") or r.get("Title") or ""

        date_obj = r.get("Date")
        if isinstance(date_obj, dict):
            date_start = date_obj.get("start") or ""
        else:
            date_start = str(date_obj or "")

        summary = r.get("Summary") or ""
        if isinstance(summary, str) and max_summary_chars > 0:
            summary = summary.strip()
            if len(summary) > max_summary_chars:
                summary = summary[: max_summary_chars - 3].rstrip() + "..."

        tags = r.get("Tags")
        if isinstance(tags, list):
            tags_list = [str(t) for t in tags if t]
        elif isinstance(tags, str) and tags:
            tags_list = [tags]
        else:
            tags_list = []

        source_url = r.get("URL") or ""
        notion_url = r.get("url") or ""
        items.append(
            {
                "title": title,
                "date": date_start,
                "summary": summary,
                "tags": tags_list,
                "source_url": source_url,
                "notion_url": notion_url,
            }
        )
    return items


def _cleanup_text(text: str) -> str:
    text = (text or "").replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _count_lines(text: str) -> int:
    return len((text or "").splitlines())


def _compress_to_line_limit(text: str, line_limit: int) -> str:
    if not text:
        return ""
    compressed = chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "너는 편집자다. 아래 글을 의미를 유지하면서 줄 수를 줄여라.\n"
                    f"- 반드시 {line_limit}줄 이하\n"
                    "- 한국어, 플레인 텍스트\n"
                    "- 마크다운 금지, 이모지 금지\n"
                    "- 불필요한 빈 줄/장식 제거\n"
                ),
            },
            {"role": "user", "content": text},
        ],
        max_tokens=900,
        temperature=0.2,
    )
    return _cleanup_text(compressed or text)


def _summarize_monthly(
    tab_label: str,
    year: int,
    month: int,
    items: list[dict],
    line_limit: int,
) -> str:
    payload = {
        "tab": tab_label,
        "year": year,
        "month": month,
        "items": items,
        "notes": (
            "items[].summary는 사람이 미리 적어둔 요약이다. "
            "가능하면 source_url(외부 링크)을 출처로 쓰고, 없으면 notion_url을 출처로 쓴다."
        ),
    }

    draft = chat_completion(
        [
            {
                "role": "system",
                "content": (
                    "너는 사내 인사이트 편집자다. 입력 데이터를 기반으로 월간 브리핑을 작성한다.\n"
                    f"- 출력은 최대 {line_limit}줄 (줄바꿈 기준)\n"
                    "- 한국어, 플레인 텍스트\n"
                    "- 마크다운 문법 금지\n"
                    "- 이모지/이모티콘 금지\n"
                    "- 중복 제거, 이슈(주제)별로 묶기\n"
                    "- 구조:\n"
                    "  1) 첫 줄: \"YYYY년 M월 <탭명> 브리핑\"\n"
                    "  2) 이후 반복: \"■ <이슈명>\" 1줄 + 요약 1~2줄 + \"출처: url1, url2\" 1줄\n"
                    "- 이슈는 5~8개 정도로 압축\n"
                    "- 각 이슈는 출처 줄을 반드시 포함 (가능하면 외부 링크인 source_url 사용)\n"
                    "\n"
                    "출력 예시 (형식만 참고):\n"
                    "2026년 2월 AI 브리핑\n"
                    "■ 이슈명\n"
                    "요약 1\n"
                    "출처: https://example.com/a, https://example.com/b\n"
                ),
            },
            {"role": "user", "content": json_dumps(payload)},
        ],
        max_tokens=1100,
        temperature=0.2,
    )
    text = _cleanup_text(draft)
    if _count_lines(text) <= line_limit:
        return _ensure_links_if_missing(text, items, line_limit)

    text = _compress_to_line_limit(text, line_limit)
    if _count_lines(text) <= line_limit:
        return _ensure_links_if_missing(text, items, line_limit)

    # 최후의 수단: 강제 절단 (줄 수 보장)
    return _ensure_links_if_missing("\n".join(text.splitlines()[:line_limit]).strip(), items, line_limit)


def _collect_source_urls(items: list[dict]) -> list[str]:
    urls: list[str] = []
    for it in items:
        u = (it.get("source_url") or "").strip()
        if not u:
            u = (it.get("notion_url") or "").strip()
        if not u:
            continue
        if not (u.startswith("http://") or u.startswith("https://")):
            continue
        urls.append(u)

    # De-dupe while keeping order
    seen = set()
    uniq = []
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        uniq.append(u)
    return uniq


def _ensure_links_if_missing(text: str, items: list[dict], line_limit: int) -> str:
    """If the model forgot to include any URLs, append a compact reference line."""
    if "http://" in text or "https://" in text:
        return text

    urls = _collect_source_urls(items)
    if not urls:
        return text

    appended = _cleanup_text(text.rstrip() + "\n참고 링크: " + ", ".join(urls[:6]))
    if _count_lines(appended) <= line_limit:
        return appended

    # Keep the reference line, drop earlier lines if needed.
    lines = appended.splitlines()
    if len(lines) <= line_limit:
        return appended
    ref = lines[-1]
    kept = lines[: max(0, line_limit - 1)] + [ref]
    return "\n".join(kept).strip()


def json_dumps(obj: object) -> str:
    # Avoid importing json at module top to keep the surface small.
    import json  # noqa: PLC0415

    return json.dumps(obj, ensure_ascii=False)


def try_generate_monthly_briefing(
    message: str,
    *,
    line_limit: int = 30,
    max_items: int = 60,
) -> str | None:
    """Try to generate a monthly briefing for a content tab.

    Returns:
        str: briefing text if the message matches the pattern.
        None: if not a monthly briefing request.
    """
    msg_norm = _norm(message)
    if not _looks_like_briefing_request(msg_norm):
        return None

    db_key = _resolve_content_db_key(msg_norm)
    if not db_key:
        return None

    cfg = get_domain_config("content")
    db_id = (cfg.get("databases", {}) or {}).get(db_key, "")
    if not db_id:
        tab_label = _TAB_LABELS.get(db_key, db_key)
        return f"{tab_label} 탭 데이터베이스 설정을 찾을 수 없습니다."

    now = datetime.now()
    ym = _parse_year_month(message, now) or (now.year, now.month)
    year, month = ym
    start_iso, end_iso = _month_range_iso(year, month)

    filter_obj = _build_date_filter(db_key, start_iso, end_iso)
    qr = query_database(
        db_id,
        filter_obj=filter_obj,
        sorts=[{"property": "Date", "direction": "ascending"}],
        page_size=100,
        max_results=max_items,
    )
    if not qr.get("success"):
        return f"Notion 조회 실패: {qr.get('error', 'unknown error')}"

    parsed = [parse_page_properties(p) for p in qr.get("results", [])]
    if not parsed:
        tab_label = _TAB_LABELS.get(db_key, db_key)
        return f"{year}년 {month}월 {tab_label} 탭에 저장된 콘텐츠가 없습니다."

    tab_label = _TAB_LABELS.get(db_key, db_key)
    items = _extract_items(parsed)
    return _summarize_monthly(tab_label, year, month, items, line_limit)
