#!/usr/bin/env python3
"""
wiki_utils.py — 跨 skill 共用工具（kb-ingest / kb-lint / kb-stats）。

提供：
- resolve_vault_dir(script_file): 從腳本路徑推算 vault 根目錄
- parse_frontmatter(text): 解析 YAML frontmatter，回傳 (fm_dict, body_str)
- WIKILINK_RE: wikilink 正則表達式（已編譯）
- TW_TZ: 台灣時區（UTC+8）
- format_tw_date(ts_str): ISO timestamp → YYYY-MM-DD（台灣時間）

Import 方式（在各 skill 的 scripts/*.py 中）：

    import os, sys
    sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "_lib")))
    from wiki_utils import resolve_vault_dir, parse_frontmatter, WIKILINK_RE, TW_TZ, format_tw_date
"""

import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── 時區 ──────────────────────────────────────────────────────────────────────

TW_TZ = timezone(timedelta(hours=8))

# ── Wikilink ──────────────────────────────────────────────────────────────────

WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')

# ── wiki/ 頂層非內容檔（hot/index/log/overview 不視為內容頁）──────────────────

TOP_LEVEL_SKIP = {"hot.md", "index.md", "log.md", "overview.md"}


# ── 路徑工具 ──────────────────────────────────────────────────────────────────

def resolve_vault_dir(script_file: str) -> str:
    """從腳本的 __file__ 推算 vault 根目錄。

    腳本位置：<vault>/.claude/skills/<skill>/scripts/<script>.py
    路徑結構：scripts/(1) → <skill>/(2) → skills/(3) → .claude/(4) → <vault>/(5)
    """
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.abspath(script_file))
                )
            )
        )
    )


# ── Frontmatter ───────────────────────────────────────────────────────────────

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """解析 YAML frontmatter，回傳 (fm_dict, body)。

    支援：
    - key: value（字串）
    - key: [a, b, c]（行內列表）
    - key:\\n  - item（多行列表）
    - 縮排的 nested dict 欄位（直接略過，不解析）
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].strip()
    fm: dict = {}
    current_key: str | None = None
    current_list: list | None = None
    for line in fm_text.splitlines():
        if re.match(r'^  - ', line) and current_list is not None:
            val = line[4:].strip().strip('"').strip("'")
            current_list.append(val)
        elif not line.startswith(" ") and ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val == "":
                current_key = key
                current_list = []
                fm[key] = current_list
            elif val.startswith("[") and val.endswith("]"):
                items = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
                fm[key] = items
                current_list = None
                current_key = None
            else:
                fm[key] = val
                current_list = None
                current_key = None
        elif line.startswith("  ") and current_key and current_list is None:
            pass  # nested dict，略過
    return fm, body


# ── 日期工具 ──────────────────────────────────────────────────────────────────

def format_tw_date(ts_str: str) -> str:
    """ISO timestamp（含 Z / +00:00 等）→ YYYY-MM-DD（台灣時間 UTC+8）。

    無法解析時，回傳前 10 字元（通常已是日期格式）或空字串。
    """
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).astimezone(TW_TZ)
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        import sys
        print(f"[WARN] format_tw_date({ts_str!r}): {e}", file=sys.stderr)
        return ts_str[:10] if ts_str and len(ts_str) >= 10 else ""


# ── Source 解析工具 ────────────────────────────────────────────────────────────

def extract_fm_text(text: str) -> str:
    """回傳 frontmatter --- 之間的原文（不含分隔符），供逐行處理用。"""
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[3:end].strip()


def parse_source_blocks(fm_text: str) -> list:
    """從 frontmatter 原文提取 sources 條目，回傳 [{"session": str, "has_transcript": bool}]。"""
    blocks = []
    current = None
    for line in fm_text.splitlines():
        m = re.match(r'^\s+- session:\s*(\S+)', line)
        if m:
            if current:
                blocks.append(current)
            current = {"session": m.group(1), "has_transcript": False}
        elif current and re.match(r'^\s+transcript:', line):
            current["has_transcript"] = True
    if current:
        blocks.append(current)
    return blocks


# ── Wiki 內容頁面掃描 ─────────────────────────────────────────────────────────

def collect_content_pages(wiki_dir, today=None) -> list[dict]:
    """掃描 wiki_dir/ 收集所有「內容頁面」（排除 _index.md、頂層工具檔、meta/）。"""
    if today is None:
        today = datetime.now(TW_TZ).date()
    SUBDIR_SKIP = {"_index.md"}
    pages = []
    for md_path in Path(wiki_dir).rglob("*.md"):
        rel = md_path.relative_to(wiki_dir)
        parts = rel.parts
        if len(parts) == 1 and parts[0] in TOP_LEVEL_SKIP:
            continue
        if parts[-1] in SUBDIR_SKIP:
            continue
        if parts[0] == "meta":
            continue

        try:
            text = md_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"[WARN] collect_content_pages read {md_path}: {e}", file=sys.stderr)
            continue

        fm, body = parse_frontmatter(text)
        fm_text = extract_fm_text(text)

        updated_str = fm.get("updated", fm.get("created", ""))
        updated_date = None
        if updated_str:
            try:
                from datetime import date as _date
                updated_date = _date.fromisoformat(str(updated_str).strip())
            except ValueError:
                pass

        has_tldrs = bool(re.search(r'^##\s+TL;DR', body, re.MULTILINE))
        source_blocks = parse_source_blocks(fm_text)

        pages.append({
            "path": str(rel),
            "type": fm.get("type", "unknown"),
            "status": fm.get("status", "draft"),
            "confidence": fm.get("confidence", ""),
            "updated": updated_date,
            "has_tldr": has_tldrs,
            "source_count": len(source_blocks),
            "source_blocks": source_blocks,
        })
    return pages
