#!/usr/bin/env python3
"""
Generate token usage statistics and conversation category reports for Claude Code.
Outputs a Markdown report with Mermaid pie charts (no extra packages required).

Usage:
  python3 generate_stats.py --projects ~/.claude/projects --days 7 --out report.md
"""

import json
import re
import argparse
import time
import os
import importlib.util
from pathlib import Path
from datetime import datetime, timezone, timedelta


def _load_lang():
    env_path = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "devtools-plugins", "export-chat-logs", ".env"
    )
    lang = "en"
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("PLUGIN_LANG="):
                    lang = line.split("=", 1)[1].strip().strip("'\"")
                    break
    except Exception:
        pass
    lang_file = lang.replace("-", "_")
    i18n_dir = os.path.join(os.path.dirname(__file__), "i18n")
    locale_path = os.path.join(i18n_dir, f"{lang_file}.py")
    if not os.path.exists(locale_path):
        locale_path = os.path.join(i18n_dir, "en.py")
    spec = importlib.util.spec_from_file_location("_locale", locale_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.S


def _load_tz():
    env_path = os.path.join(
        os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config")),
        "devtools-plugins", "export-chat-logs", ".env"
    )
    offset = 8  # Default UTC+8
    try:
        with open(env_path) as f:
            for line in f:
                if line.startswith("TIMEZONE_OFFSET="):
                    offset = int(line.split("=", 1)[1].strip())
                    break
    except Exception:
        pass
    return timezone(timedelta(hours=offset)), offset


TZ_LOCAL, TZ_OFFSET = _load_tz()
TZ_LABEL = f"UTC{TZ_OFFSET:+d}"
S = _load_lang()

# Category keywords (matched against title + first few user messages)
CATEGORIES = {
    "Coding": [
        "code", "function", "implement", "class", "feature", "create", "build",
        "write", "add", "api", "endpoint", "component", "module", "script",
    ],
    "Debugging": [
        "debug", "error", "bug", "fix", "issue", "broken", "fail", "crash",
        "not work", "wrong", "problem", "traceback", "exception",
    ],
    "Config": [
        "config", "setup", "install", "hook", "setting", "env", "configure",
        "deploy", "docker", "ci", "cd", "pipeline", "workflow",
    ],
    "Docs": [
        "explain", "document", "readme", "comment", "how", "what", "why",
        "describe", "summary", "help", "guide",
    ],
    "Refactoring": [
        "refactor", "optimize", "improve", "clean", "restructure", "performance",
        "simplify", "reorganize",
    ],
}


def categorize(title, first_messages):
    text = (title or "").lower()
    for role, content, _ in first_messages[:5]:
        if role == "user":
            text += " " + content[:300].lower()

    scores = {cat: 0 for cat in CATEGORIES}
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                scores[cat] += 1

    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other"


def extract_session_stats(filepath):
    """Extract exact token usage from a Claude Code JSONL file."""
    title = None
    input_tokens = 0
    output_tokens = 0
    cache_tokens = 0
    first_messages = []
    first_ts = None
    last_ts = None

    try:
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if obj.get("type") == "custom-title":
                    t = obj.get("customTitle", "").strip()
                    if t:
                        title = t

                ts = obj.get("timestamp", "")
                if ts and first_ts is None:
                    first_ts = ts
                if ts:
                    last_ts = ts

                if obj.get("isMeta"):
                    continue

                msg = obj.get("message", {})
                role = msg.get("role", "")

                usage = msg.get("usage", {})
                if usage:
                    input_tokens  += usage.get("input_tokens", 0)
                    output_tokens += usage.get("output_tokens", 0)
                    cache_tokens  += (usage.get("cache_read_input_tokens", 0)
                                    + usage.get("cache_creation_input_tokens", 0))

                if role in ("user", "assistant") and len(first_messages) < 6:
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        text = content.strip()
                    elif isinstance(content, list):
                        parts = [b.get("text", "") for b in content
                                 if isinstance(b, dict) and b.get("type") == "text"]
                        text = " ".join(parts).strip()
                    else:
                        text = ""
                    if text:
                        first_messages.append((role, text, ts))

    except Exception:
        pass

    return {
        "title":          title,
        "first_ts":       first_ts,
        "last_ts":        last_ts,
        "input_tokens":   input_tokens,
        "output_tokens":  output_tokens,
        "cache_tokens":   cache_tokens,
        "first_messages": first_messages,
        "estimated":      False,
    }


def find_recent_jsonl(projects_dir, days):
    cutoff = time.time() - days * 86400
    results = []
    if not Path(projects_dir).is_dir():
        return results
    for jsonl in Path(projects_dir).rglob("*.jsonl"):
        parts = set(jsonl.parts)
        if "subagents" in parts or "memory" in parts:
            continue
        try:
            if jsonl.stat().st_mtime >= cutoff:
                results.append(jsonl)
        except OSError:
            pass
    return results


# ── Report generation ──────────────────────────────────────────────────────────

def fmt(n):
    return f"{n:,}"


def mermaid_pie(title, data):
    lines = ["```mermaid", f"pie title {title}"]
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        if value > 0:
            lines.append(f'    "{label}" : {value}')
    lines.append("```")
    return "\n".join(lines)


def ascii_bar(data, total, width=24):
    lines = []
    for label, value in sorted(data.items(), key=lambda x: -x[1]):
        if value == 0:
            continue
        pct = value / total * 100 if total else 0
        bar_len = int(pct / 100 * width)
        bar = "█" * bar_len + "░" * (width - bar_len)
        lines.append(f"`{bar}` {pct:5.1f}%  {label}")
    return "\n".join(lines)


def generate_report(sessions, days, out_path):
    now_str    = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
    start_date = (datetime.now(TZ_LOCAL) - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date   = datetime.now(TZ_LOCAL).strftime("%Y-%m-%d")

    sessions.sort(key=lambda s: s["first_ts"] or "", reverse=True)

    total_input  = sum(s["input_tokens"]  for s in sessions)
    total_output = sum(s["output_tokens"] for s in sessions)
    total_cache  = sum(s["cache_tokens"]  for s in sessions)
    total_all    = total_input + total_output

    cat_input  = {}
    cat_output = {}
    cat_count  = {}
    for s in sessions:
        c = s["category"]
        cat_input[c]  = cat_input.get(c, 0)  + s["input_tokens"]
        cat_output[c] = cat_output.get(c, 0) + s["output_tokens"]
        cat_count[c]  = cat_count.get(c, 0)  + 1

    cat_total = {c: cat_input.get(c, 0) + cat_output.get(c, 0) for c in cat_count}

    L = []
    L += [
        f"# {S['report_title']}", "",
        f"**{S['label_period']}:** {start_date} – {end_date} (last {days} days)",
        f"**{S['label_generated']}:** {now_str}",
        f"**{S['label_sessions']}:** {len(sessions)}",
        "", "---", "",
    ]

    # Summary
    L += [
        f"## {S['section_summary']}", "",
        f"| {S['col_item']} | {S['col_count']} |",
        "|------|-----:|",
        f"| {S['row_input']} | {fmt(total_input)} |",
        f"| {S['row_output']} | {fmt(total_output)} |",
        f"| {S['row_cache']} | {fmt(total_cache)} |",
        f"| **{S['row_total']}** | **{fmt(total_all)}** |",
        "",
    ]
    if total_all > 0:
        in_pct  = total_input  / total_all * 100
        out_pct = total_output / total_all * 100
        L.append(f"> {S['summary_ratio'].format(in_pct=in_pct, out_pct=out_pct)}")
        L.append("")
    L += ["---", ""]

    # Conversation type distribution
    L += [f"## {S['section_type_dist']}", ""]
    L.append(mermaid_pie(S["pie_type_sessions"], cat_count))
    L.append("")
    if total_all > 0:
        # Mermaid pie uses localized display labels
        cat_total_display = {S.get(f"cat_{k}", k): v for k, v in cat_total.items()}
        L.append(mermaid_pie(S["pie_tokens_by_cat"], cat_total_display))
        L.append("")

    if cat_count:
        cat_count_display = {S.get(f"cat_{k}", k): v for k, v in cat_count.items()}
        L += [
            "<details>",
            f"<summary>{S['ascii_label']}</summary>", "",
            S["ascii_session_dist"],
            ascii_bar(cat_count_display, len(sessions)),
            "",
        ]
        if total_all > 0:
            L += [
                S["ascii_token_dist"],
                ascii_bar(cat_total_display, total_all),
                "",
            ]
        L += ["</details>", ""]

    # Category breakdown
    L += [
        f"### {S['section_cat_breakdown']}", "",
        f"| {S['col_category']} | {S['col_sessions']} | {S['col_input']} | {S['col_output']} | {S['col_total']} | {S['col_share']} |",
        "|------|:--------:|----------:|----------:|-----:|-----:|",
    ]
    for cat in sorted(cat_count, key=lambda c: -cat_count.get(c, 0)):
        ci  = cat_input.get(cat, 0)
        co  = cat_output.get(cat, 0)
        ct  = ci + co
        pct = ct / total_all * 100 if total_all else 0
        cat_disp = S.get(f"cat_{cat}", cat)
        L.append(f"| {cat_disp} | {cat_count[cat]} | {fmt(ci)} | {fmt(co)} | {fmt(ct)} | {pct:.1f}% |")
    L += ["", "---", ""]

    # Session details
    has_model_col = any(s.get("models") for s in sessions)
    if sessions:
        if has_model_col:
            L += [
                f"## {S['section_session_details']}", "",
                f"| {S['col_datetime']} | {S['col_title']} | {S['col_category']} | {S['col_model']} | {S['col_input']} | {S['col_output']} | {S['col_total']} |",
                "|----------|------|------|------|-----:|-----:|-----:|",
            ]
        else:
            L += [
                f"## {S['section_session_details']}", "",
                f"| {S['col_datetime']} | {S['col_title']} | {S['col_category']} | {S['col_input']} | {S['col_output']} | {S['col_total']} |",
                "|----------|------|------|-----:|-----:|-----:|",
            ]
        for s in sessions:
            ts_str = ""
            if s["first_ts"]:
                try:
                    dt = datetime.fromisoformat(s["first_ts"].replace("Z", "+00:00")).astimezone(TZ_LOCAL)
                    ts_str = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    ts_str = (s["first_ts"] or "")[:16]
            title_display = (s["title"] or S["untitled"])[:40]
            total_s = s["input_tokens"] + s["output_tokens"]
            cat_disp = S.get(f"cat_{s['category']}", s['category'])
            if has_model_col:
                model_str = ", ".join(s.get("models") or []) or "-"
                L.append(
                    f"| {ts_str} | {title_display} | {cat_disp}"
                    f" | {model_str}"
                    f" | {fmt(s['input_tokens'])} | {fmt(s['output_tokens'])} | {fmt(total_s)} |"
                )
            else:
                L.append(
                    f"| {ts_str} | {title_display} | {cat_disp}"
                    f" | {fmt(s['input_tokens'])} | {fmt(s['output_tokens'])} | {fmt(total_s)} |"
                )
        L.append("")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(L), encoding="utf-8")
    print(S["msg_stats_done"].format(sessions=len(sessions), tokens=fmt(total_all), path=out_path))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projects", required=True, help="Claude Code projects directory")
    parser.add_argument("--days",  type=int, default=7)
    parser.add_argument("--out",   required=True)
    args = parser.parse_args()

    jsonl_files = find_recent_jsonl(args.projects, args.days)
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=args.days)
    sessions = []
    for fp in jsonl_files:
        s = extract_session_stats(fp)
        active_ts = s["last_ts"] or s["first_ts"]
        if not active_ts:
            continue  # Skip empty sessions with no message timestamps
        try:
            dt = datetime.fromisoformat(active_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            if dt < cutoff_dt:
                continue  # last_ts out of range, skip (consistent with convert_to_markdown.py)
        except Exception:
            pass
        s["category"] = categorize(s["title"], s["first_messages"])
        sessions.append(s)

    if not sessions:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(f"# {S['report_title']}\n\n{S['no_sessions_found']}\n", encoding="utf-8")
        print(S["warn_no_files"])
        return

    generate_report(sessions, args.days, args.out)


if __name__ == "__main__":
    main()
