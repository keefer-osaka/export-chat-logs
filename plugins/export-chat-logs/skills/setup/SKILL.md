---
name: setup
description: "Configure Telegram Bot Token, chat ID, timezone, language, output format, and Cowork inclusion for the export-chat-logs plugin."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Configure Telegram

## Step 1 — Read current configuration

Read `~/.config/devtools-plugins/export-chat-logs/.env` (use `$HOME` if `~` doesn't work) to extract the raw values. If the file does not exist, all values are unset and this is a first-time setup.

Extract these values from the .env:
- `CURRENT_TOKEN` (mask it: show first 6 and last 4 characters, e.g. `123456...F4x2`)
- `CURRENT_CHAT_ID`
- `CURRENT_TZ` (format as `UTC+N`)
- `CURRENT_LANG` (default: `en` if not set)
- `CURRENT_FORMAT`
- `CURRENT_COWORK`

## Step 2 — Determine language (`SETUP_LANG`)

- **First-time** (`.env` does not exist): ask the user to pick a language (see below). Set `SETUP_LANG` to the result.
- **Reconfigure** (`.env` exists): Set `SETUP_LANG = CURRENT_LANG` (internal only — do not display this assignment). Skip to Step 3.

**Language selection (first-time only) — this is the only trilingual question:**
```json
{
  "questions": [{
    "question": "Select language / 選擇語言 / 言語を選択",
    "header": "Language",
    "multiSelect": false,
    "options": [
      {
        "label": "English",
        "description": "All output in English"
      },
      {
        "label": "繁體中文",
        "description": "所有輸出使用繁體中文"
      },
      {
        "label": "日本語",
        "description": "すべての出力を日本語で表示"
      }
    ]
  }]
}
```

Answer mapping: `"English"` → `en`, `"繁體中文"` → `zh-TW`, `"日本語"` → `ja`

**After Step 2, read the questions file for the selected language:**

```
Read "${CLAUDE_PLUGIN_ROOT}/skills/setup/questions/<SETUP_LANG>.json"
```

(e.g. if `SETUP_LANG` is `zh-TW`, read `questions/zh-TW.json`)

Store the parsed JSON as `Q`. All subsequent AskUserQuestion calls use keys from `Q`, substituting `<PLACEHOLDER>` values with the actual current values extracted in Step 1.

**All subsequent AskUserQuestion calls use `SETUP_LANG`.**

---

## Step 3 — Menu (existing config only)

Use `Q["menu"]` — substitute all `<CURRENT_*>` and `<MASKED_TOKEN>` placeholders with actual values. Use AskUserQuestion with `multiSelect: true`.

If a value is not set, use the phrase "not set" / "未設定" / "未設定" in the description.

For unselected settings, use `skip` when calling `save-config.sh`. **Do NOT call AskUserQuestion for unselected steps — skip those steps entirely and go straight to Step 8.**

---

## Step 4 — Language (if "Language" / "語言" / "言語" selected in reconfigure)

Language was already set in Step 2 for first-time. For reconfigure, show this step only if Language was selected in the menu.

Use `Q["language"]`.

Answer mapping: `"English"` → `en`, `"繁體中文"` → `zh-TW`, `"日本語"` → `ja`

---

## Step 5 — Bot Token (if selected or first-time)

If `CURRENT_TOKEN` exists: use `Q["bot_token_exists"]` (substitute `<MASKED_TOKEN>`).
Otherwise: use `Q["bot_token_first_time"]`.

**Handling answers:**
- User types via text field → use that text as the token
- "Keep current" label from Q → use `skip`
- "Skip for now" label from Q → use `skip`
- "How to get a token" label from Q → print `Q["bot_token_help"]`, then ask Step 5 again

---

## Step 6 — Chat ID (if selected or first-time)

If `CURRENT_CHAT_ID` exists: use `Q["chat_id_exists"]` (substitute `<CURRENT_CHAT_ID>`).
Otherwise: use `Q["chat_id_first_time"]`.

**Handling answers:**
- User types via text field → use that text as the Chat ID
- "Keep current" label from Q → use `skip`
- "Skip for now" label from Q → use `skip`
- "How to get Chat ID" label from Q → print `Q["chat_id_help"]`, then ask Step 6 again

---

## Step 7 — Preferences (if "Preferences" / "偏好設定" / "環境設定" selected, or first-time)

Use `Q["preferences"]` — ask 3 questions (Timezone + Format + Cowork) in a single AskUserQuestion call.

Append `(current)` / `（目前）` / `（現在）` to the option matching the current value.

---

## Step 8 — Map answers and save

Map the collected answers to config values:

| Answer | Value |
|--------|-------|
| "Keep current" / "保留現值" / "現在の値を保持" | `skip` |
| "Skip for now" / "稍後設定" / "後で設定する" | `skip` |
| Token / Chat ID typed via text field | use as-is |
| "UTC+8" | `8` |
| "UTC+9" | `9` |
| "UTC-5" | `-5` |
| "UTC-8" | `-8` |
| Timezone typed via text field (e.g. `-5`, `5`) | use as-is |
| "English" | `en` |
| "繁體中文" | `zh-TW` |
| "日本語" | `ja` |
| "HTML" | `html` |
| "Markdown" | `md` |
| "Yes" / "是" / "はい" | `true` |
| "No" / "否" / "いいえ" | `false` |
| First-time language (from Step 2) | use for `lang` argument |
| Language not selected in menu | `skip` for lang |
| Preferences not selected in menu | `skip` for tz, format, cowork |
| Setting not selected in menu | `skip` |

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-config.sh" "<token or skip>" "<chat_id or skip>" "<timezone or skip>" "<lang or skip>" "<format or skip>" "<include_cowork or skip>"
```

Stop after configuration is complete — do not proceed with the export flow.
