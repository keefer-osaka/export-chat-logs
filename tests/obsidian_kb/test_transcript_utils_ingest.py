import sys
import os

_base = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/kb-ingest/scripts'))
sys.path.insert(0, os.path.join(_base, '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

import json
import pytest
import transcript_utils as tu


# ── TestMakeSlug ───────────────────────────────────────────────────────────────

class TestMakeSlug:
    def test_empty_returns_untitled(self):
        assert tu.make_slug("") == "untitled"

    def test_plain_english_lowercased_kebab(self):
        result = tu.make_slug("Hello World")
        assert result == "hello-world"

    def test_parentheses_stripped(self):
        result = tu.make_slug("foo (bar)")
        assert "bar" not in result
        assert result.startswith("foo")

    def test_max_len_respected(self):
        long_text = "a" * 80
        result = tu.make_slug(long_text, max_len=40)
        assert len(result) <= 40

    def test_cjk_preserved(self):
        result = tu.make_slug("測試標題")
        assert "測試標題" in result or "測試" in result


# ── TestMakeTranscriptFilename ─────────────────────────────────────────────────

class TestMakeTranscriptFilename:
    def test_returns_md_extension(self):
        result = tu.make_transcript_filename("2026-04-11T10:00:00Z", "abcdefgh1234", "My Title")
        assert result.endswith(".md")

    def test_contains_first_8_chars_of_session_id(self):
        session_id = "abcdefgh1234567890"
        result = tu.make_transcript_filename("2026-04-11T10:00:00Z", session_id, "My Title")
        assert "abcdefgh" in result

    def test_empty_session_id_uses_unknown(self):
        result = tu.make_transcript_filename("2026-04-11T10:00:00Z", "", "Some Title")
        assert "unknown" in result


# ── TestFormatMessageHeader ────────────────────────────────────────────────────

class TestFormatMessageHeader:
    def test_user_role_produces_user_label(self):
        result = tu.format_message_header("user", "2026-04-11T14:32:00Z")
        assert result.startswith("## User")

    def test_assistant_role_produces_assistant_label(self):
        result = tu.format_message_header("assistant", "2026-04-11T14:32:00Z")
        assert result.startswith("## Assistant")

    def test_valid_iso_ts_formatted_date_in_output(self):
        result = tu.format_message_header("user", "2026-04-11T14:32:00Z")
        assert "2026-04-11" in result

    def test_bad_ts_falls_back_gracefully(self):
        result = tu.format_message_header("user", "not-a-date")
        # falls back to ts value or "?"
        assert "not-a-date" in result or "?" in result


# ── TestRenderTranscriptMd ─────────────────────────────────────────────────────

class TestRenderTranscriptMd:
    def _render(self, **kwargs):
        defaults = dict(
            session_id="sess-id-1234",
            title="Test Title",
            cwd="/some/path",
            date="2026-04-11",
            first_ts="2026-04-11T10:00:00Z",
            last_ts="2026-04-11T11:00:00Z",
            message_count=2,
            last_processed_msg_uuid="uuid-last",
            last_processed_at="2026-04-11T11:00:00Z",
            models=["claude-3-5-sonnet"],
            derived_pages=[],
            status="processed",
            messages=[],
            author="",
            source="jsonl",
        )
        defaults.update(kwargs)
        return tu.render_transcript_md(**defaults)

    def test_contains_frontmatter_delimiters(self):
        result = self._render()
        assert result.count("---") >= 2

    def test_session_id_in_frontmatter(self):
        result = self._render(session_id="my-session-xyz")
        assert "my-session-xyz" in result

    def test_messages_rendered_with_role_headers(self):
        messages = [
            {"role": "user", "text": "Hello there", "timestamp": "2026-04-11T10:00:00Z", "uuid": "u1"},
            {"role": "assistant", "text": "Hi back", "timestamp": "2026-04-11T10:01:00Z", "uuid": "a1"},
        ]
        result = self._render(messages=messages)
        assert "## User" in result
        assert "## Assistant" in result
        assert "Hello there" in result
        assert "Hi back" in result

    def test_empty_messages_no_role_headers(self):
        result = self._render(messages=[])
        # Only the title heading should appear, no ## User or ## Assistant
        assert "## User" not in result
        assert "## Assistant" not in result

    def test_author_line_present_when_provided(self):
        result = self._render(author="keefer")
        assert "author: keefer" in result

    def test_author_line_absent_when_empty(self):
        result = self._render(author="")
        assert "author:" not in result

    def test_delta_marker_present_at_end(self):
        result = self._render(last_processed_msg_uuid="uuid-abc")
        assert "<!-- delta marker: last_processed_msg_uuid=uuid-abc -->" in result


# ── TestParseFrontmatterSources ────────────────────────────────────────────────

class TestParseFrontmatterSources:
    def test_empty_content_returns_empty_list(self):
        assert tu._parse_frontmatter_sources("") == []

    def test_no_sources_key_returns_empty_list(self):
        content = "---\ntitle: My Page\n---\nBody text"
        assert tu._parse_frontmatter_sources(content) == []

    def test_sources_block_with_session_ids_returned(self):
        content = (
            "---\n"
            "title: My Page\n"
            "sources:\n"
            "  - session: abc-session-1\n"
            "    date: 2026-04-11\n"
            "  - session: def-session-2\n"
            "    date: 2026-04-12\n"
            "---\nBody"
        )
        result = tu._parse_frontmatter_sources(content)
        assert "abc-session-1" in result
        assert "def-session-2" in result


# ── TestReadWriteSessionsJson ──────────────────────────────────────────────────

class TestReadWriteSessionsJson:
    def test_missing_file_returns_empty_dict(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tu, "SESSIONS_JSON_PATH", str(tmp_path / "nonexistent.json"))
        assert tu.read_sessions_json() == {}

    def test_corrupt_json_returns_empty_dict(self, monkeypatch, tmp_path):
        bad = tmp_path / "sessions.json"
        bad.write_text("{ not valid json }", encoding="utf-8")
        monkeypatch.setattr(tu, "SESSIONS_JSON_PATH", str(bad))
        assert tu.read_sessions_json() == {}

    def test_write_then_read_roundtrip(self, monkeypatch, tmp_path):
        path = tmp_path / "_schema" / "sessions.json"
        monkeypatch.setattr(tu, "SESSIONS_JSON_PATH", str(path))
        data = {"sess-1": {"status": "processed", "message_count": 5}}
        tu.write_sessions_json(data)
        result = tu.read_sessions_json()
        assert result == data

    def test_write_creates_parent_dirs(self, monkeypatch, tmp_path):
        path = tmp_path / "deep" / "nested" / "sessions.json"
        monkeypatch.setattr(tu, "SESSIONS_JSON_PATH", str(path))
        tu.write_sessions_json({"x": 1})
        assert path.exists()


# ── TestUpsertSessionManifest ──────────────────────────────────────────────────

class TestUpsertSessionManifest:
    def _call(self, manifest, session_id="sess-1", **kwargs):
        defaults = dict(
            transcript_path="transcripts/foo.md",
            last_processed_msg_uuid="uuid-1",
            last_processed_ts="2026-04-11T10:00:00Z",
            message_count=3,
            status="processed",
            derived_pages=[],
            author="",
            source="jsonl",
            author_conflict=False,
        )
        defaults.update(kwargs)
        tu.upsert_session_manifest(manifest, session_id, **defaults)

    def test_new_session_added_to_empty_manifest(self):
        manifest = {}
        self._call(manifest)
        assert "sess-1" in manifest
        assert manifest["sess-1"]["status"] == "processed"

    def test_existing_derived_pages_merged(self):
        manifest = {"sess-1": {"derived_pages": ["wiki/page-a.md"], "status": "processed"}}
        self._call(manifest, derived_pages=["wiki/page-b.md"])
        pages = manifest["sess-1"]["derived_pages"]
        assert "wiki/page-a.md" in pages
        assert "wiki/page-b.md" in pages

    def test_cross_author_conflict_detected(self):
        manifest = {"sess-1": {"author": "alice", "derived_pages": []}}
        self._call(manifest, author="bob")
        assert manifest["sess-1"].get("author_conflict") is True

    def test_author_field_absent_when_empty(self):
        manifest = {}
        self._call(manifest, author="")
        assert "author" not in manifest["sess-1"]

    def test_source_field_written(self):
        manifest = {}
        self._call(manifest, source="export")
        assert manifest["sess-1"]["source"] == "export"


# ── TestScanWikiSources ────────────────────────────────────────────────────────

class TestScanWikiSources:
    def _make_wiki_page(self, wiki_dir, name, sessions):
        """Create a wiki page with given session IDs in its sources frontmatter."""
        sources_block = "".join(
            f"  - session: {s}\n    date: 2026-04-11\n" for s in sessions
        )
        content = (
            "---\n"
            "title: Test Page\n"
            f"sources:\n{sources_block}"
            "---\nBody text\n"
        )
        p = wiki_dir / name
        p.write_text(content, encoding="utf-8")

    def test_returns_session_ids_from_pages(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        self._make_wiki_page(wiki_dir, "page1.md", ["sess-aaa"])
        result = tu.scan_wiki_sources(str(wiki_dir))
        assert "sess-aaa" in result

    def test_multiple_pages_multiple_entries(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        self._make_wiki_page(wiki_dir, "page1.md", ["sess-aaa"])
        self._make_wiki_page(wiki_dir, "page2.md", ["sess-bbb"])
        result = tu.scan_wiki_sources(str(wiki_dir))
        assert "sess-aaa" in result
        assert "sess-bbb" in result

    def test_page_with_no_sources_not_included(self, tmp_path):
        wiki_dir = tmp_path / "wiki"
        wiki_dir.mkdir()
        content = "---\ntitle: No Sources\n---\nJust body text.\n"
        (wiki_dir / "nosrc.md").write_text(content, encoding="utf-8")
        result = tu.scan_wiki_sources(str(wiki_dir))
        assert result == {}


# ── TestFindJsonlFiles ─────────────────────────────────────────────────────────

class TestFindJsonlFiles:
    def test_empty_dir_returns_empty_list(self, monkeypatch, tmp_path):
        monkeypatch.setattr(tu, "PROJECTS_DIR", str(tmp_path))
        result = tu.find_jsonl_files()
        assert result == []

    def test_jsonl_file_found(self, monkeypatch, tmp_path):
        proj = tmp_path / "my-project"
        proj.mkdir()
        (proj / "session.jsonl").write_text('{"type":"message"}\n', encoding="utf-8")
        monkeypatch.setattr(tu, "PROJECTS_DIR", str(tmp_path))
        result = tu.find_jsonl_files()
        assert any("session.jsonl" in r for r in result)

    def test_subagents_subdir_excluded(self, monkeypatch, tmp_path):
        proj = tmp_path / "my-project"
        subagents = proj / "subagents"
        subagents.mkdir(parents=True)
        (subagents / "agent.jsonl").write_text('{"type":"message"}\n', encoding="utf-8")
        monkeypatch.setattr(tu, "PROJECTS_DIR", str(tmp_path))
        result = tu.find_jsonl_files()
        assert not any("subagents" in r for r in result)


# ── TestGetLastMessageUuid ─────────────────────────────────────────────────────

class TestGetLastMessageUuid:
    def _write_jsonl(self, path, lines):
        with open(path, "w", encoding="utf-8") as f:
            for obj in lines:
                f.write(json.dumps(obj) + "\n")

    def test_empty_file_returns_empty_string(self, tmp_path):
        p = tmp_path / "empty.jsonl"
        p.write_text("", encoding="utf-8")
        assert tu.get_last_message_uuid(str(p)) == ""

    def test_only_meta_lines_returns_empty_string(self, tmp_path):
        p = tmp_path / "meta.jsonl"
        self._write_jsonl(p, [
            {"isMeta": True, "uuid": "meta-uuid", "message": {"role": "user"}},
        ])
        assert tu.get_last_message_uuid(str(p)) == ""

    def test_last_user_message_uuid_returned(self, tmp_path):
        p = tmp_path / "session.jsonl"
        self._write_jsonl(p, [
            {"uuid": "uuid-1", "message": {"role": "user", "content": "hello"}},
            {"uuid": "uuid-2", "message": {"role": "assistant", "content": "hi"}},
            {"uuid": "uuid-3", "message": {"role": "user", "content": "bye"}},
        ])
        assert tu.get_last_message_uuid(str(p)) == "uuid-3"

    def test_mixed_roles_last_wins(self, tmp_path):
        p = tmp_path / "mixed.jsonl"
        self._write_jsonl(p, [
            {"uuid": "uid-a", "message": {"role": "user", "content": "first"}},
            {"uuid": "uid-b", "message": {"role": "assistant", "content": "second"}},
        ])
        assert tu.get_last_message_uuid(str(p)) == "uid-b"
