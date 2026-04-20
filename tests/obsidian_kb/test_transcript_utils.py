import sys
import os

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import json
import re
from unittest.mock import patch, MagicMock
import pytest

import transcript_utils as tu


# ── make_slug ─────────────────────────────────────────────────────────────────

def test_make_slug_basic():
    assert tu.make_slug("Hello World") == "hello-world"


def test_make_slug_empty():
    assert tu.make_slug("") == "untitled"


def test_make_slug_none_like():
    assert tu.make_slug("   ") == "untitled"


def test_make_slug_removes_parens():
    assert tu.make_slug("My Topic (extra)") == "my-topic"


def test_make_slug_removes_full_width_parens():
    assert tu.make_slug("主題（括號內）說明") == "主題說明"


def test_make_slug_max_len():
    long = "a" * 100
    result = tu.make_slug(long, max_len=10)
    assert len(result) <= 10


def test_make_slug_collapses_dashes():
    assert "--" not in tu.make_slug("foo   bar")


# ── make_transcript_filename ──────────────────────────────────────────────────

def test_make_transcript_filename_structure():
    fname = tu.make_transcript_filename("2026-04-10T06:00:00Z", "abcdef1234567890", "My Chat")
    assert fname.startswith("2026-04-10-abcdef12-")
    assert fname.endswith(".md")


def test_make_transcript_filename_short_session():
    fname = tu.make_transcript_filename("2026-04-10T06:00:00Z", "abc", "title")
    assert "abc" in fname


def test_make_transcript_filename_bad_ts():
    fname = tu.make_transcript_filename("not-a-timestamp", "sid123456", "title")
    assert fname.endswith(".md")
    assert "sid12345" in fname


# ── format_message_header ─────────────────────────────────────────────────────

def test_format_message_header_user():
    header = tu.format_message_header("user", "2026-04-10T06:00:00Z")
    assert header.startswith("## User (")
    assert "2026-04-10" in header


def test_format_message_header_assistant():
    header = tu.format_message_header("assistant", "2026-04-10T06:00:00Z")
    assert header.startswith("## Assistant (")


def test_format_message_header_bad_ts():
    header = tu.format_message_header("user", "bad-ts")
    assert "User" in header
    assert "bad-ts" in header


# ── render_transcript_md ──────────────────────────────────────────────────────

def _make_messages():
    return [
        {"role": "user", "text": "Hello", "timestamp": "2026-04-10T06:00:00Z", "uuid": "u1"},
        {"role": "assistant", "text": "Hi there", "timestamp": "2026-04-10T06:01:00Z", "uuid": "u2"},
    ]


def test_render_transcript_md_frontmatter():
    md = tu.render_transcript_md(
        session_id="sess-001",
        title="Test Session",
        cwd="/tmp",
        date="2026-04-10",
        first_ts="2026-04-10T06:00:00Z",
        last_ts="2026-04-10T06:01:00Z",
        message_count=2,
        last_processed_msg_uuid="u2",
        last_processed_at="2026-04-10T06:02:00Z",
        models=["claude-3"],
        derived_pages=["wiki/page.md"],
        status="processed",
        messages=_make_messages(),
    )
    assert md.startswith("---")
    assert "session_id: sess-001" in md
    assert "title: Test Session" in md
    assert "status: processed" in md


def test_render_transcript_md_body_contains_messages():
    md = tu.render_transcript_md(
        session_id="sess-002",
        title="Chat",
        cwd="/tmp",
        date="2026-04-10",
        first_ts="2026-04-10T06:00:00Z",
        last_ts="2026-04-10T06:01:00Z",
        message_count=2,
        last_processed_msg_uuid="u2",
        last_processed_at="2026-04-10T06:02:00Z",
        models=[],
        derived_pages=[],
        status="processed",
        messages=_make_messages(),
    )
    assert "Hello" in md
    assert "Hi there" in md
    assert "## User" in md
    assert "## Assistant" in md


def test_render_transcript_md_delta_marker():
    md = tu.render_transcript_md(
        session_id="s", title="t", cwd="/", date="2026-04-10",
        first_ts="2026-04-10T06:00:00Z", last_ts="2026-04-10T06:00:00Z",
        message_count=1, last_processed_msg_uuid="uuid-abc",
        last_processed_at="2026-04-10T06:00:00Z",
        models=[], derived_pages=[], status="raw",
        messages=[{"role": "user", "text": "hi", "timestamp": "2026-04-10T06:00:00Z"}],
    )
    assert "<!-- delta marker: last_processed_msg_uuid=uuid-abc -->" in md


def test_render_transcript_md_skips_empty_messages():
    messages = [
        {"role": "user", "text": "", "timestamp": "2026-04-10T06:00:00Z"},
        {"role": "assistant", "text": "Response", "timestamp": "2026-04-10T06:01:00Z"},
    ]
    md = tu.render_transcript_md(
        session_id="s", title="t", cwd="/", date="2026-04-10",
        first_ts="2026-04-10T06:00:00Z", last_ts="2026-04-10T06:01:00Z",
        message_count=1, last_processed_msg_uuid="", last_processed_at="",
        models=[], derived_pages=[], status="raw", messages=messages,
    )
    assert "## User" not in md
    assert "Response" in md


def test_render_transcript_md_author_line():
    md = tu.render_transcript_md(
        session_id="s", title="t", cwd="/", date="2026-04-10",
        first_ts="", last_ts="", message_count=0, last_processed_msg_uuid="",
        last_processed_at="", models=[], derived_pages=[], status="raw",
        messages=[], author="keefer",
    )
    assert "author: keefer" in md


# ── upsert_session_manifest ───────────────────────────────────────────────────

def test_upsert_session_manifest_new_entry():
    manifest = {}
    tu.upsert_session_manifest(
        manifest, "sid-1", "transcripts/foo.md", "uuid-last", "2026-04-10T06:00:00Z",
        5, "processed", ["wiki/a.md"]
    )
    assert "sid-1" in manifest
    entry = manifest["sid-1"]
    assert entry["transcript_path"] == "transcripts/foo.md"
    assert entry["message_count"] == 5
    assert "wiki/a.md" in entry["derived_pages"]


def test_upsert_session_manifest_merges_derived_pages():
    manifest = {"sid-1": {"derived_pages": ["wiki/a.md"], "author": ""}}
    tu.upsert_session_manifest(
        manifest, "sid-1", "transcripts/foo.md", "uuid-last", "2026-04-10T06:00:00Z",
        5, "processed", ["wiki/b.md"]
    )
    assert "wiki/a.md" in manifest["sid-1"]["derived_pages"]
    assert "wiki/b.md" in manifest["sid-1"]["derived_pages"]


def test_upsert_session_manifest_author_conflict():
    manifest = {"sid-1": {"derived_pages": [], "author": "alice"}}
    tu.upsert_session_manifest(
        manifest, "sid-1", "transcripts/foo.md", "uuid-last", "2026-04-10T06:00:00Z",
        3, "processed", [], author="bob"
    )
    assert manifest["sid-1"].get("author_conflict") is True


def test_upsert_session_manifest_no_conflict_same_author():
    manifest = {"sid-1": {"derived_pages": [], "author": "alice"}}
    tu.upsert_session_manifest(
        manifest, "sid-1", "transcripts/foo.md", "uuid-last", "2026-04-10T06:00:00Z",
        3, "processed", [], author="alice"
    )
    assert not manifest["sid-1"].get("author_conflict")


# ── read_sessions_json / write_sessions_json ──────────────────────────────────

def test_read_sessions_json_missing(tmp_path):
    with patch.object(tu, "SESSIONS_JSON_PATH", str(tmp_path / "sessions.json")):
        result = tu.read_sessions_json()
    assert result == {}


def test_write_and_read_sessions_json(tmp_path):
    path = str(tmp_path / "sessions.json")
    data = {"sid-1": {"transcript_path": "foo.md"}}
    with patch.object(tu, "SESSIONS_JSON_PATH", path):
        tu.write_sessions_json(data)
        result = tu.read_sessions_json()
    assert result == data


def test_read_sessions_json_invalid_json(tmp_path):
    path = tmp_path / "sessions.json"
    path.write_text("not json", encoding="utf-8")
    with patch.object(tu, "SESSIONS_JSON_PATH", str(path)):
        result = tu.read_sessions_json()
    assert result == {}


# ── append_delta_to_transcript ────────────────────────────────────────────────

def _make_base_transcript(session_id="sess-1", last_uuid="old-uuid"):
    return f"""---
session_id: {session_id}
title: Test
cwd: /tmp
date: 2026-04-10
first_ts: 2026-04-10T06:00:00Z
last_ts: 2026-04-10T06:00:00Z
message_count: 1
last_processed_msg_uuid: {last_uuid}
last_processed_at: 2026-04-10T06:00:00Z
models: []
derived_pages: []
status: raw
source: jsonl
---

# Test

> Session `sess-000`｜2026-04-10｜1 messages

## User (2026-04-10 14:00)

Hello

---

<!-- delta marker: last_processed_msg_uuid={last_uuid} -->
"""


def test_append_delta_adds_messages(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    content = _make_base_transcript()
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_msgs = [{"role": "assistant", "text": "New response", "timestamp": "2026-04-10T07:00:00Z"}]
    result = tu.append_delta_to_transcript(transcript_path, new_msgs, "new-uuid")

    assert result is True
    updated = open(transcript_path, encoding="utf-8").read()
    assert "New response" in updated
    assert "new-uuid" in updated


def test_append_delta_updates_frontmatter(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    content = _make_base_transcript(last_uuid="old-uuid")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_msgs = [{"role": "user", "text": "Follow-up", "timestamp": "2026-04-10T07:00:00Z"}]
    tu.append_delta_to_transcript(transcript_path, new_msgs, "new-uuid-123")

    updated = open(transcript_path, encoding="utf-8").read()
    assert "last_processed_msg_uuid: new-uuid-123" in updated
    assert "status: processed" in updated


def test_append_delta_no_marker_returns_false(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write("# No marker here\n\nSome content\n")

    result = tu.append_delta_to_transcript(transcript_path, [{"role": "user", "text": "hi", "timestamp": ""}], "uuid")
    assert result is False


def test_append_delta_empty_messages_returns_false(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    content = _make_base_transcript()
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)

    result = tu.append_delta_to_transcript(transcript_path, [], "new-uuid")
    assert result is False


def test_append_delta_skips_empty_text(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    content = _make_base_transcript()
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_msgs = [{"role": "user", "text": "   ", "timestamp": "2026-04-10T07:00:00Z"}]
    result = tu.append_delta_to_transcript(transcript_path, new_msgs, "new-uuid")
    assert result is False


def test_append_delta_increments_message_count(tmp_path):
    transcript_path = str(tmp_path / "transcript.md")
    content = _make_base_transcript()
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(content)

    new_msgs = [
        {"role": "user", "text": "msg1", "timestamp": "2026-04-10T07:00:00Z"},
        {"role": "assistant", "text": "msg2", "timestamp": "2026-04-10T07:01:00Z"},
    ]
    tu.append_delta_to_transcript(transcript_path, new_msgs, "new-uuid")
    updated = open(transcript_path, encoding="utf-8").read()
    assert "message_count: 3" in updated


# ── rebuild_transcripts_index ─────────────────────────────────────────────────

def test_rebuild_transcripts_index(tmp_path):
    td = tmp_path / "transcripts"
    td.mkdir()
    (td / "2026-04-10-abcdef12-test.md").write_text(
        "---\nsession_id: abcdef1234567890\ntitle: My Chat\ndate: 2026-04-10\nstatus: processed\n---\n\nBody\n",
        encoding="utf-8",
    )
    tu.rebuild_transcripts_index(str(td))
    index = (td / "_index.md").read_text(encoding="utf-8")
    assert "My Chat" in index
    assert "2026-04-10" in index
    assert "processed" in index


def test_rebuild_transcripts_index_skips_index_file(tmp_path):
    td = tmp_path / "transcripts"
    td.mkdir()
    (td / "_index.md").write_text("# old index\n", encoding="utf-8")
    tu.rebuild_transcripts_index(str(td))
    index = (td / "_index.md").read_text(encoding="utf-8")
    assert "Transcripts Index" in index


def test_rebuild_transcripts_index_sorted_desc(tmp_path):
    td = tmp_path / "transcripts"
    td.mkdir()
    for date in ["2026-03-01", "2026-04-10", "2026-02-15"]:
        (td / f"{date}-aabbccdd-chat.md").write_text(
            f"---\nsession_id: aabbccdd1234\ntitle: Chat {date}\ndate: {date}\nstatus: raw\n---\n\nBody\n",
            encoding="utf-8",
        )
    tu.rebuild_transcripts_index(str(td))
    index = (td / "_index.md").read_text(encoding="utf-8")
    pos_apr = index.find("2026-04-10")
    pos_mar = index.find("2026-03-01")
    pos_feb = index.find("2026-02-15")
    assert pos_apr < pos_mar < pos_feb


# ── get_last_message_uuid ─────────────────────────────────────────────────────

def test_get_last_message_uuid(tmp_path):
    jsonl = tmp_path / "session.jsonl"
    lines = [
        json.dumps({"uuid": "u1", "message": {"role": "user"}}),
        json.dumps({"uuid": "u2", "message": {"role": "assistant"}}),
        json.dumps({"isMeta": True, "uuid": "meta-u3", "message": {"role": "user"}}),
    ]
    jsonl.write_text("\n".join(lines), encoding="utf-8")
    result = tu.get_last_message_uuid(str(jsonl))
    assert result == "u2"


def test_get_last_message_uuid_missing_file():
    result = tu.get_last_message_uuid("/nonexistent/path.jsonl")
    assert result == ""


def test_get_last_message_uuid_skips_meta(tmp_path):
    jsonl = tmp_path / "session.jsonl"
    lines = [
        json.dumps({"uuid": "u1", "message": {"role": "user"}}),
        json.dumps({"isMeta": True, "uuid": "meta-u2", "message": {"role": "user"}}),
    ]
    jsonl.write_text("\n".join(lines), encoding="utf-8")
    result = tu.get_last_message_uuid(str(jsonl))
    assert result == "u1"


def test_get_last_message_uuid_empty_file(tmp_path):
    jsonl = tmp_path / "empty.jsonl"
    jsonl.write_text("", encoding="utf-8")
    result = tu.get_last_message_uuid(str(jsonl))
    assert result == ""


# ── scan_wiki_sources ─────────────────────────────────────────────────────────

def test_scan_wiki_sources(tmp_path):
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    page = wiki_dir / "page.md"
    page.write_text(
        "---\nsources:\n  - session: sid-abc\n    date: 2026-04-10\n---\n\nBody\n",
        encoding="utf-8",
    )
    result = tu.scan_wiki_sources(str(wiki_dir))
    assert "sid-abc" in result
    assert any("page.md" in p for p in result["sid-abc"])


def test_scan_wiki_sources_empty_dir(tmp_path):
    wiki_dir = tmp_path / "wiki"
    wiki_dir.mkdir()
    result = tu.scan_wiki_sources(str(wiki_dir))
    assert result == {}


# ── add_transcript_to_wiki_sources ────────────────────────────────────────────

def _make_wiki_page(session_id="sid-001", has_transcript=False):
    transcript_line = f'    transcript: "[[2026-04-10-sid-001-chat]]"\n' if has_transcript else ""
    return f"""---
title: My Page
sources:
  - session: {session_id}
    date: 2026-04-10
{transcript_line}created: 2026-04-10
---

Body text here.
"""


def test_add_transcript_adds_field(tmp_path):
    wiki_path = str(tmp_path / "page.md")
    with open(wiki_path, "w", encoding="utf-8") as f:
        f.write(_make_wiki_page("sid-001", has_transcript=False))

    result = tu.add_transcript_to_wiki_sources(
        wiki_path, {"sid-001": "transcripts/2026-04-10-sid-001-chat.md"}
    )
    assert result is True
    content = open(wiki_path, encoding="utf-8").read()
    assert 'transcript:' in content
    assert "2026-04-10-sid-001-chat" in content


def test_add_transcript_no_change_if_already_present(tmp_path):
    wiki_path = str(tmp_path / "page.md")
    with open(wiki_path, "w", encoding="utf-8") as f:
        f.write(_make_wiki_page("sid-001", has_transcript=True))

    result = tu.add_transcript_to_wiki_sources(
        wiki_path, {"sid-001": "transcripts/2026-04-10-sid-001-chat.md"}
    )
    assert result is False


def test_add_transcript_no_match_returns_false(tmp_path):
    wiki_path = str(tmp_path / "page.md")
    with open(wiki_path, "w", encoding="utf-8") as f:
        f.write(_make_wiki_page("sid-001"))

    result = tu.add_transcript_to_wiki_sources(wiki_path, {"other-sid": "transcripts/foo.md"})
    assert result is False


def test_add_transcript_no_frontmatter_returns_false(tmp_path):
    wiki_path = str(tmp_path / "page.md")
    with open(wiki_path, "w", encoding="utf-8") as f:
        f.write("# No frontmatter\n\nJust body.\n")

    result = tu.add_transcript_to_wiki_sources(wiki_path, {"sid-001": "foo.md"})
    assert result is False
