#!/usr/bin/env python3
"""
Convert Claude Code JSONL chat logs to human-readable Markdown format.
Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--days N]
"""

import json
import re
import sys
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

MAX_MSG_LEN = 3000  # Max characters to display per message


def truncate(text, max_len=MAX_MSG_LEN):
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n\n" + S["truncated"].format(n=len(text) - max_len)


def clean_string_content(text):
    """Clean string message content: strip control characters, simplify slash command XML."""
    # Strip control characters
    text = re.sub(r'[\x00-\x08\x0b-\x1f\x7f]', '', text).strip()

    # <local-command-stdout>...</local-command-stdout> → skip (return empty)
    if re.match(r'<local-command-stdout>', text):
        return ''

    # <command-name>/CMD</command-name>...<command-message>MSG</command-message>... → compact output
    if re.match(r'<command-name>', text) or re.match(r'<command-message>', text):
        msg_m = re.search(r'<command-message>(.*?)</command-message>', text, re.DOTALL)
        name_m = re.search(r'<command-name>(.*?)</command-name>', text, re.DOTALL)
        if msg_m:
            msg = msg_m.group(1).strip()
            if msg:
                return f"/{msg}"
        if name_m:
            return name_m.group(1).strip()
        return ''

    return text


def extract_text_blocks(content):
    """Extract only text-type blocks from a content array."""
    if isinstance(content, str):
        return clean_string_content(content)
    if not isinstance(content, list):
        return ""
    parts = []
    for block in content:
        if not isinstance(block, dict):
            continue
        t = block.get("type", "")
        if t == "text":
            text = clean_string_content(block.get("text", ""))
            if text:
                parts.append(text)
        # tool_result, tool_use, thinking, image are all skipped
    return "\n\n".join(parts)


def convert_claude_jsonl(filepath):
    """Parse a Claude Code session JSONL file. Returns (messages, first_ts, last_ts, title, cwd, models)."""
    messages = []
    first_ts = None
    last_ts = None
    title = None
    cwd = None
    models_seen = []

    with open(filepath, encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            # Get conversation title from custom-title (use last entry, as it may have been renamed)
            if obj.get("type") == "custom-title":
                t = obj.get("customTitle", "").strip()
                if t:
                    title = t

            msg = obj.get("message", {})
            role = msg.get("role", "")
            if role not in ("user", "assistant"):
                continue

            # Skip meta messages injected from CLAUDE.md / skills
            if obj.get("isMeta"):
                continue

            # Get timestamp and cwd
            ts = obj.get("timestamp", "")
            if ts and first_ts is None:
                first_ts = ts
            if ts:
                last_ts = ts
            if cwd is None:
                cwd = obj.get("cwd", "")

            # Collect model info (only present in assistant messages)
            if role == "assistant":
                model = msg.get("model", "")
                if model and model not in models_seen:
                    models_seen.append(model)

            content = msg.get("content", "")
            text = extract_text_blocks(content)

            if text.strip():
                messages.append((role, text.strip(), ts))

    return messages, first_ts, last_ts, title, cwd, models_seen


def generate_title_from_messages(messages):
    """Generate a title from conversation content (used for unnamed sessions)."""
    for role, text, ts in messages:
        if role == "user" and text.strip():
            first_line = text.strip().split('\n')[0].strip()
            # Strip common markdown and command prefixes
            first_line = re.sub(r'[#*`_~\[\]<>]', '', first_line).strip()
            first_line = re.sub(r'^[@!]', '', first_line).strip()
            if len(first_line) > 3:
                return first_line[:60]
    return None


def format_markdown(messages, first_ts, cwd=None, title=None, models=None):
    lines = []

    # Parse date
    date_str = ""
    if first_ts:
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).astimezone(TZ_LOCAL)
            date_str = dt.strftime("%Y-%m-%d %H:%M") + f" {TZ_LABEL}"
        except Exception:
            date_str = first_ts

    # Title
    display_title = title or "Claude Code"
    lines.append(f"# {display_title}")
    lines.append("")

    if date_str:
        lines.append(f"**{S['label_date']}:** {date_str}")

    # Project path: show folder name (absolute path)
    if cwd:
        folder_name = Path(cwd).name or cwd
        lines.append(f"**{S['label_project']}:** {folder_name} (`{cwd}`)")

    lines.append(f"**{S['label_source']}:** {S['source_name']}")
    if models:
        lines.append(f"**{S['label_model']}:** {', '.join(models)}")
    lines.append(f"**{S['label_messages']}:** {len(messages)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    if not messages:
        lines.append(S["no_messages"])
        return "\n".join(lines)

    for role, text, ts in messages:
        ts_str = ""
        if ts:
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                ts_str = f" · {dt.astimezone(TZ_LOCAL).strftime('%Y-%m-%d %H:%M')} {TZ_LABEL}"
            except Exception:
                pass
        if role == "user":
            lines.append(f"### {S['role_user']}{ts_str}")
        else:
            lines.append(f"### {S['role_assistant']}{ts_str}")
        lines.append("")
        lines.append(truncate(text))
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def make_output_path(out_dir, first_ts, title):
    """Generate output filename based on date and title."""
    if first_ts:
        try:
            dt = datetime.fromisoformat(first_ts.replace("Z", "+00:00")).astimezone(TZ_LOCAL)
            date_str = f"{dt.strftime('%Y-%m-%d_%H-%M-%S')}-{dt.microsecond // 1000:03d}"
        except Exception:
            date_str = "unknown"
    else:
        date_str = "unknown"

    if title:
        title_safe = re.sub(r'[^\w\-]', '_', title)[:60].strip('_')
        filename = f"{date_str}_{title_safe}.md"
    else:
        filename = f"{date_str}.md"
    return os.path.join(out_dir, filename)


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 convert_to_markdown.py <input.jsonl> <output_dir> [--days N]")
        sys.exit(1)

    input_path = sys.argv[1]
    out_dir = sys.argv[2]
    days_filter = None

    if "--days" in sys.argv:
        idx = sys.argv.index("--days")
        if idx + 1 < len(sys.argv):
            try:
                days_filter = int(sys.argv[idx + 1])
            except ValueError:
                pass

    messages, first_ts, last_ts, title, cwd, models = convert_claude_jsonl(input_path)

    # If no timestamp, fall back to file modification time (local timezone)
    if not first_ts:
        mtime = os.path.getmtime(input_path)
        dt_mtime = datetime.fromtimestamp(mtime, tz=TZ_LOCAL)
        first_ts = dt_mtime.isoformat()

    # Always use the last timestamp (covers long conversations, resume, compact, etc.)
    active_ts = last_ts or first_ts

    # Apply --days filter if provided
    if days_filter is not None and active_ts:
        try:
            dt_check = datetime.fromisoformat(active_ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_filter)
            if dt_check < cutoff:
                sys.exit(0)
        except Exception:
            pass

    md = format_markdown(messages, active_ts, cwd=cwd, title=title, models=models)

    os.makedirs(out_dir, exist_ok=True)
    output_path = make_output_path(out_dir, active_ts, title)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(S["msg_done_convert"].format(n=len(messages), path=output_path))


if __name__ == "__main__":
    main()
