import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/export-chat-logs/scripts'))

import html as _html

import pytest

import generate_stats as gs


def _make_session(**overrides):
    base = {
        "category": "Coding",
        "input_tokens": 100,
        "output_tokens": 50,
        "cache_read": 0,
        "cache_creation": 0,
        "tool_counts": {},
        "project": "proj",
        "models": [],
        "first_ts": "2026-01-01T00:00:00Z",
        "last_ts": "2026-01-01T00:10:00Z",
        "title": "Some chat",
        "first_user_message": "",
        "messages": [],
        "duration": 120,
        "filepath": "/tmp/fake.jsonl",
        "cwd": "/home/user/proj",
    }
    base.update(overrides)
    return base


class TestCategorize:
    def test_coding_keyword(self):
        assert gs.categorize("Implement a new function", []) == "Coding"

    def test_debug_keyword(self):
        assert gs.categorize("fix crash on startup", []) == "Debugging"

    def test_no_match_returns_other(self):
        assert gs.categorize("xyzzy", []) == "Other"

    def test_counts_user_messages(self):
        msgs = [("user", "please debug this traceback", "")]
        assert gs.categorize("", msgs) == "Debugging"

    def test_ignores_assistant_messages(self):
        msgs = [("assistant", "debug error bug fix", "")]
        assert gs.categorize("", msgs) == "Other"

    def test_truncates_long_user_message(self):
        long_msg = "x" * 400 + " debug error bug fix"
        msgs = [("user", long_msg, "")]
        assert gs.categorize("", msgs) == "Other"


class TestFmt:
    def test_thousands(self):
        assert gs.fmt(1000) == "1,000"

    def test_millions(self):
        assert gs.fmt(1234567) == "1,234,567"

    def test_small(self):
        assert gs.fmt(42) == "42"

    def test_zero(self):
        assert gs.fmt(0) == "0"


class TestFmtDuration:
    def test_under_minute(self):
        assert gs.fmt_duration(45) == "< 1m"

    def test_minutes(self):
        assert gs.fmt_duration(300) == "5m"

    def test_hours_and_mins(self):
        assert gs.fmt_duration(3600 + 120) == "1h 2m"

    def test_hours_only(self):
        assert gs.fmt_duration(7200) == "2h"

    def test_boundary_59s(self):
        assert gs.fmt_duration(59) == "< 1m"


class TestComputeStats:
    def test_single_session(self):
        d = gs._compute_stats([_make_session(input_tokens=10, output_tokens=5)])
        assert d["total_input"] == 10
        assert d["total_output"] == 5
        assert d["total_all"] == 15
        assert d["cat_count"]["Coding"] == 1

    def test_multi_category(self):
        sessions = [
            _make_session(category="Coding",    input_tokens=100, output_tokens=50),
            _make_session(category="Debugging", input_tokens=20,  output_tokens=10),
        ]
        d = gs._compute_stats(sessions)
        assert d["cat_input"]["Coding"] == 100
        assert d["cat_input"]["Debugging"] == 20
        assert d["cat_count"]["Coding"] == 1
        assert d["cat_total"]["Coding"] == 150
        assert d["cat_total"]["Debugging"] == 30

    def test_tool_aggregation(self):
        sessions = [
            _make_session(tool_counts={"Read": 3, "Bash": 1}),
            _make_session(tool_counts={"Read": 2}),
        ]
        d = gs._compute_stats(sessions)
        assert d["tool_totals"]["Read"] == 5
        assert d["tool_totals"]["Bash"] == 1

    def test_project_aggregation(self):
        sessions = [
            _make_session(project="alpha", input_tokens=10, output_tokens=20),
            _make_session(project="beta",  input_tokens=5,  output_tokens=5),
            _make_session(project="alpha", input_tokens=1,  output_tokens=0),
        ]
        d = gs._compute_stats(sessions)
        assert d["proj_tokens"]["alpha"] == 31
        assert d["proj_sessions"]["alpha"] == 2
        assert d["proj_sessions"]["beta"] == 1

    def test_model_aggregation(self):
        sessions = [
            _make_session(models=["sonnet", "opus"]),
            _make_session(models=["sonnet"]),
        ]
        d = gs._compute_stats(sessions)
        assert d["model_sessions"]["sonnet"] == 2
        assert d["model_sessions"]["opus"] == 1

    def test_cache_totals(self):
        sessions = [
            _make_session(cache_read=100, cache_creation=50),
            _make_session(cache_read=200, cache_creation=25),
        ]
        d = gs._compute_stats(sessions)
        assert d["total_cache_read"] == 300
        assert d["total_cache_creation"] == 75

    def test_unknown_project_default(self):
        s = _make_session()
        s.pop("project")
        d = gs._compute_stats([s])
        assert "Unknown" in d["proj_tokens"]


class TestMermaidLabel:
    def test_angle_brackets(self):
        assert gs._mermaid_label("<foo>") == "(foo)"

    def test_plain(self):
        assert gs._mermaid_label("hello") == "hello"

    def test_mixed(self):
        assert gs._mermaid_label("a<b>c") == "a(b)c"


class TestMermaidPie:
    def test_has_header(self):
        out = gs.mermaid_pie("Test", {"a": 1})
        assert out.startswith("```mermaid")
        assert "pie title Test" in out
        assert out.endswith("```")

    def test_omits_zero(self):
        out = gs.mermaid_pie("T", {"keep": 1, "drop": 0})
        assert "keep" in out
        assert '"drop"' not in out

    def test_sorted_desc(self):
        out = gs.mermaid_pie("T", {"low": 1, "high": 10})
        lines = out.splitlines()
        high_idx = next(i for i, l in enumerate(lines) if "high" in l)
        low_idx  = next(i for i, l in enumerate(lines) if "low" in l)
        assert high_idx < low_idx


class TestAsciiBar:
    def test_proportional(self):
        out = gs.ascii_bar({"a": 50}, 100, width=10)
        assert "50.0%" in out
        assert out.count("█") == 5

    def test_omits_zero(self):
        out = gs.ascii_bar({"a": 10, "b": 0}, 10)
        assert "a" in out
        # b has value 0 so should be omitted entirely
        lines = [l for l in out.splitlines() if l.strip()]
        assert len(lines) == 1

    def test_zero_total(self):
        out = gs.ascii_bar({"a": 0}, 0)
        assert out == ""


class TestHtmlTable:
    def test_headers_and_rows(self):
        out = gs._html_table(["A", "B"], [["1", "2"], ["3", "4"]])
        assert out.count("</th>") == 2
        assert out.count("<td") == 4
        assert "<thead>" in out and "<tbody>" in out

    def test_col_classes(self):
        out = gs._html_table(["A"], [["x"]], col_classes=["num"])
        assert 'class="num"' in out

    def test_escapes_html(self):
        out = gs._html_table(["A"], [["<script>"]])
        assert "<script>" not in out
        assert "&lt;script&gt;" in out


class TestBarChartHtml:
    def test_contains_container(self):
        out = gs._bar_chart_html({"a": 1}, 1)
        assert 'class="bar-chart"' in out

    def test_percentage_computed(self):
        out = gs._bar_chart_html({"a": 25}, 100)
        assert "25.0%" in out

    def test_show_count_true(self):
        out = gs._bar_chart_html({"a": 42}, 100, show_count=True)
        assert "bar-val" in out
        assert "42" in out

    def test_show_count_false(self):
        out = gs._bar_chart_html({"a": 42}, 100, show_count=False)
        assert "bar-val" not in out

    def test_escapes_label(self):
        out = gs._bar_chart_html({"<evil>": 1}, 1)
        assert "<evil>" not in out
        assert "&lt;evil&gt;" in out


class TestPrepareSessionRows:
    def test_has_model_col_false_when_no_models(self):
        has_model, rows = gs._prepare_session_rows([_make_session(models=[])])
        assert has_model is False
        assert len(rows) == 1

    def test_has_model_col_true(self):
        sessions = [_make_session(models=[]), _make_session(models=["sonnet"])]
        has_model, rows = gs._prepare_session_rows(sessions)
        assert has_model is True

    def test_missing_first_ts(self):
        has_model, rows = gs._prepare_session_rows([_make_session(first_ts=None)])
        assert rows[0]["ts"] == ""

    def test_duration_formatted(self):
        has_model, rows = gs._prepare_session_rows([_make_session(duration=300)])
        assert rows[0]["dur"] == "5m"

    def test_duration_missing(self):
        s = _make_session()
        s["duration"] = None
        has_model, rows = gs._prepare_session_rows([s])
        assert rows[0]["dur"] == "-"

    def test_title_truncated_to_40(self):
        long_title = "x" * 80
        has_model, rows = gs._prepare_session_rows([_make_session(title=long_title)])
        assert len(rows[0]["title"]) <= 40

    def test_totals_summed(self):
        has_model, rows = gs._prepare_session_rows(
            [_make_session(input_tokens=7, output_tokens=3)]
        )
        assert rows[0]["total"] == 10


class TestPrepareReportData:
    def test_all_keys_present(self):
        r = gs._prepare_report_data([_make_session()], days=7, source_label=None)
        for key in ("now_str", "start_date", "end_date", "report_title",
                    "total_input", "total_output", "total_all",
                    "hit_rate_str", "cat_input", "cat_output",
                    "cat_count", "cat_total", "tool_totals",
                    "proj_tokens", "proj_sessions", "model_sessions"):
            assert key in r

    def test_hit_rate_na_without_cache(self):
        r = gs._prepare_report_data(
            [_make_session(cache_read=0, cache_creation=0)], days=7, source_label=None
        )
        assert r["hit_rate_str"] == "N/A"

    def test_hit_rate_computed(self):
        r = gs._prepare_report_data(
            [_make_session(cache_read=50, cache_creation=50)], days=7, source_label=None
        )
        assert "%" in r["hit_rate_str"]

    def test_cowork_label_title(self):
        r_cowork = gs._prepare_report_data([_make_session()], 7, source_label="cowork")
        r_plain  = gs._prepare_report_data([_make_session()], 7, source_label=None)
        # cowork label should map to a different report_title entry
        assert r_cowork["report_title"] != r_plain["report_title"]


class TestGenerateReportSmoke:
    def test_md_report_written(self, tmp_path, capsys):
        out = tmp_path / "report.md"
        gs.generate_report([_make_session()], days=7, out_path=str(out))
        assert out.exists()
        captured = capsys.readouterr()
        assert "SESSIONS=1" in captured.out

    def test_html_report_written(self, tmp_path, capsys):
        out = tmp_path / "report.html"
        gs.generate_html_report([_make_session()], days=7, out_path=str(out))
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "<html" in content
        assert "</html>" in content

    def test_md_contains_sessions_table(self, tmp_path):
        out = tmp_path / "report.md"
        gs.generate_report([_make_session(title="MyTitle")], days=7, out_path=str(out))
        content = out.read_text(encoding="utf-8")
        assert "MyTitle" in content

    def test_empty_sessions_handled(self, tmp_path):
        # empty sessions still get a report written via main path;
        # generate_report itself requires >=1 session for _prepare_session_rows,
        # but _compute_stats handles empty without crash.
        d = gs._compute_stats([])
        assert d["total_all"] == 0
