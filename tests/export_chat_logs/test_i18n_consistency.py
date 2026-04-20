import sys
import os
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../plugins/export-chat-logs/scripts'))

from i18n import en, zh_TW, ja

_LOCALES = {"en": en, "zh_TW": zh_TW, "ja": ja}


class TestI18nConsistency:
    def test_keys_equal(self):
        en_keys = set(en.S)
        zh_keys = set(zh_TW.S)
        ja_keys = set(ja.S)
        assert en_keys == zh_keys, (
            f"zh_TW missing: {en_keys - zh_keys}, extra: {zh_keys - en_keys}"
        )
        assert en_keys == ja_keys, (
            f"ja missing: {en_keys - ja_keys}, extra: {ja_keys - en_keys}"
        )

    def test_all_values_nonempty_str(self):
        for locale, mod in _LOCALES.items():
            for key, val in mod.S.items():
                assert isinstance(val, str), f"[{locale}] {key!r} value is not a str"
                assert val.strip(), f"[{locale}] {key!r} value is empty"

    def test_placeholder_consistency(self):
        def placeholders(s):
            return set(re.findall(r'\{[^}]+\}', s))

        for key in en.S:
            en_ph = placeholders(en.S[key])
            for locale, mod in _LOCALES.items():
                lc_ph = placeholders(mod.S[key])
                assert en_ph == lc_ph, (
                    f"[{locale}] key {key!r}: en has {en_ph}, {locale} has {lc_ph}"
                )

    def test_high_risk_key_placeholders(self):
        for locale, mod in _LOCALES.items():
            assert "{sessions}" in mod.S["msg_stats_done"], \
                f"[{locale}] msg_stats_done missing {{sessions}}"
            assert "{tokens}" in mod.S["msg_stats_done"], \
                f"[{locale}] msg_stats_done missing {{tokens}}"
            assert "{path}" in mod.S["msg_stats_done"], \
                f"[{locale}] msg_stats_done missing {{path}}"
            assert "{in_pct:.1f}" in mod.S["summary_ratio"], \
                f"[{locale}] summary_ratio missing {{in_pct:.1f}}"
            assert "{out_pct:.1f}" in mod.S["summary_ratio"], \
                f"[{locale}] summary_ratio missing {{out_pct:.1f}}"
            assert "{n}" in mod.S["msg_done_convert"], \
                f"[{locale}] msg_done_convert missing {{n}}"
            assert "{path}" in mod.S["msg_done_convert"], \
                f"[{locale}] msg_done_convert missing {{path}}"
