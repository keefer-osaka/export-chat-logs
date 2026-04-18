#!/usr/bin/env python3
"""
update_overview.py — kb-ingest 步驟 5.1
就地更新 wiki/overview.md 的 ## 狀態 機械段，並輸出 JSON 供 LLM 判斷敘事段。
"""

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib")))
from wiki_utils import resolve_vault_dir, format_tw_date, collect_content_pages, TW_TZ  # noqa: E402

from datetime import datetime

VAULT_DIR = Path(resolve_vault_dir(__file__))
OVERVIEW_PATH = VAULT_DIR / "wiki" / "overview.md"
SESSIONS_PATH = VAULT_DIR / "_schema" / "sessions.json"
WATERMARK_PATH = VAULT_DIR / "_schema" / ".watermark"
TRANSCRIPTS_DIR = VAULT_DIR / "transcripts"


def main():
    if not OVERVIEW_PATH.exists():
        print("[WARN] wiki/overview.md not found — skipping update", file=sys.stderr)
        sys.exit(0)

    content = OVERVIEW_PATH.read_text(encoding="utf-8")

    # Preserve 初始化日期
    init_date = "未知"
    m = re.search(r'初始化日期\*\*[：:]\s*(.+)', content)
    if m:
        init_date = m.group(1).strip()

    # Compute stats
    pages = collect_content_pages(VAULT_DIR / "wiki")
    total_pages = len(pages)
    from collections import Counter
    type_counts = Counter(p["type"] for p in pages)

    # Type breakdown string
    type_parts = [f"{t}: {n}" for t, n in sorted(type_counts.items()) if t != "unknown"]
    if type_counts.get("unknown"):
        type_parts.append(f"unknown: {type_counts['unknown']}")
    type_str = "、".join(type_parts) if type_parts else "（無）"

    # Last ingest + sessions count from sessions.json
    last_ingest = "（尚未執行）"
    sessions_count = 0
    if SESSIONS_PATH.exists():
        try:
            data = json.loads(SESSIONS_PATH.read_text(encoding="utf-8"))
            sessions_count = len(data)
            if sessions_count > 0:
                last_ts = max(v.get("last_ts", "") for v in data.values() if v.get("last_ts"))
                if last_ts:
                    last_ingest = format_tw_date(last_ts)
        except Exception as e:
            print(f"[WARN] update_overview load sessions.json: {e}", file=sys.stderr)

    # Watermark
    watermark = "（未設定）"
    if WATERMARK_PATH.exists():
        watermark = WATERMARK_PATH.read_text(encoding="utf-8").strip() or watermark

    # Transcripts count
    transcripts_count = 0
    if TRANSCRIPTS_DIR.exists():
        transcripts_count = len([p for p in TRANSCRIPTS_DIR.glob("*.md") if p.name != "_index.md"])

    # Build new ## 狀態 block
    new_status_block = (
        f"## 狀態\n\n"
        f"- **初始化日期**：{init_date}\n"
        f"- **總頁面數**：{total_pages}（{type_str}）\n"
        f"- **最後 ingest**：{last_ingest}（共 {sessions_count} 個 sessions）\n"
        f"- **水位線**：{watermark}\n"
        f"- **Transcripts**：{transcripts_count} 個\n"
    )

    # Replace existing ## 狀態 section (up to next ## or EOF)
    new_content = re.sub(
        r'## 狀態\n.*?(?=\n## |\Z)',
        new_status_block,
        content,
        count=1,
        flags=re.DOTALL,
    )

    OVERVIEW_PATH.write_text(new_content, encoding="utf-8")

    result = {
        "page_count": total_pages,
        "last_ingest": last_ingest,
        "sessions_count": sessions_count,
        "type_breakdown": dict(type_counts),
        "transcripts_count": transcripts_count,
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
