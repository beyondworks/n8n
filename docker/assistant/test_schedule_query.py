import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from domains.schedule import _query_by_date, _query_by_range, _results_to_list, _search


def test_query():
    keyword = "건강검진"
    print(f"--- Searching for '{keyword}' ---")
    res = _results_to_list(_search(keyword))
    print(f"Count: {len(res)}")
    for item in res:
        print(f" - Title: {item.get('Entry name')}")
        print(f" - Date (Parsed): {item.get('Date')}")
        print(f" - Completed: {item.get('Completed')}")
        # We want to see raw date if possible, but _results_to_list parses it.
        # Let's trust the parsed one first or modify _search to return raw if needed.
    
    print("\n--- Querying wider range (2026-02-13 ~ 2026-02-15) ---")
    res_range = _results_to_list(_query_by_range("2026-02-13", "2026-02-15"))
    print(f"Count: {len(res_range)}")
    for item in res_range:
        print(f" - {item.get('Entry name')} | Date: {item.get('Date')} | Done: {item.get('Completed')}")

    print("\n--- Querying by date (2026-02-14) using _query_by_date ---")
    res_date = _results_to_list(_query_by_date("2026-02-14"))
    print(f"Count: {len(res_date)}")
    for item in res_date:
        print(f" - {item.get('Entry name')} | Done: {item.get('Completed')}")


if __name__ == "__main__":
    test_query()
