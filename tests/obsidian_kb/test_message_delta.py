import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/obsidian-kb/vault-payload/.claude/skills/_lib'))

from message_delta import filter_messages_after_uuid


def _msgs(*uuids):
    return [{"uuid": u} for u in uuids]


# ── empty pivot → full list ────────────────────────────────────────────────────

def test_empty_pivot_returns_all():
    msgs = _msgs("a", "b", "c")
    result, found = filter_messages_after_uuid(msgs, "")
    assert result == msgs
    assert found is True

def test_none_pivot_returns_all():
    msgs = _msgs("a", "b")
    result, found = filter_messages_after_uuid(msgs, None)
    assert result == msgs
    assert found is True


# ── pivot found ────────────────────────────────────────────────────────────────

def test_pivot_at_start():
    msgs = _msgs("a", "b", "c")
    result, found = filter_messages_after_uuid(msgs, "a")
    assert found is True
    assert result == _msgs("b", "c")

def test_pivot_in_middle():
    msgs = _msgs("a", "b", "c", "d")
    result, found = filter_messages_after_uuid(msgs, "b")
    assert found is True
    assert result == _msgs("c", "d")

def test_pivot_at_end():
    msgs = _msgs("a", "b", "c")
    result, found = filter_messages_after_uuid(msgs, "c")
    assert found is True
    assert result == []


# ── pivot not found ────────────────────────────────────────────────────────────

def test_pivot_not_found():
    msgs = _msgs("a", "b", "c")
    result, found = filter_messages_after_uuid(msgs, "z")
    assert found is False
    assert result == []


# ── edge cases ─────────────────────────────────────────────────────────────────

def test_empty_message_list():
    result, found = filter_messages_after_uuid([], "a")
    assert found is False
    assert result == []

def test_empty_message_list_empty_pivot():
    result, found = filter_messages_after_uuid([], "")
    assert found is True
    assert result == []

def test_message_without_uuid_key():
    msgs = [{"uuid": "a"}, {"no_uuid": True}, {"uuid": "b"}]
    result, found = filter_messages_after_uuid(msgs, "a")
    assert found is True
    assert result == [{"no_uuid": True}, {"uuid": "b"}]

def test_duplicate_uuids_stops_at_first():
    msgs = _msgs("a", "b", "a", "c")
    result, found = filter_messages_after_uuid(msgs, "a")
    assert found is True
    assert result == _msgs("b", "a", "c")
