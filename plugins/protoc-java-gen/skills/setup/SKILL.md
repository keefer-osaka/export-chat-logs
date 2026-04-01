---
name: setup
description: "Configure protoc path, project root, proto directory, and language for the protoc-java-gen plugin."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Configure protoc-java-gen

## Step 1 — Read current configuration

Read `~/.config/devtools-plugins/protoc-java-gen/.env` (use `$HOME` if `~` doesn't work).
If the file does not exist, all values are unset and this is a first-time setup.

Extract:
- `CURRENT_PROTOC_PATH`
- `CURRENT_PROJECT_ROOT`
- `CURRENT_PROTO_DIR`
- `CURRENT_LANG` (default: `en` if not set)

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
      { "label": "English", "description": "All output in English" },
      { "label": "繁體中文", "description": "所有輸出使用繁體中文" },
      { "label": "日本語", "description": "すべての出力を日本語で表示" }
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

---

## Step 3 — Menu (existing config only)

Use `Q["menu"]` — substitute all `<CURRENT_*>` placeholders with actual values. Use AskUserQuestion with `multiSelect: true`.

If a value is not set, show `(not set)` / `（未設定）` / `（未設定）` in the description.

For unselected settings, use `skip` when calling `save-config.sh`. **Do NOT call AskUserQuestion for unselected steps — skip those steps entirely and go straight to Step 8.**

---

## Step 4 — Language (if "Language" / "語言" / "言語" selected in reconfigure)

Language was already set in Step 2 for first-time. For reconfigure, show this step only if Language was selected in the menu.

Use `Q["language"]`.

**Handling answers:**
- "English" → `en`
- "繁體中文" → `zh-TW`
- "日本語" → `ja`

---

## Step 5 — Protoc Path (if selected or first-time)

If `CURRENT_PROTOC_PATH` exists: use `Q["protoc_path_exists"]` (substitute `<CURRENT_PROTOC_PATH>`).
Otherwise: use `Q["protoc_path_first_time"]`.

**Handling answers:**
- "Keep current" / "保留現值" / "現在の値を保持" → use `skip`
- Option selected → use that path as-is
- User types in text field → use that text as the path

---

## Step 6 — Project Root (if selected or first-time)

If `CURRENT_PROJECT_ROOT` exists: use `Q["project_root_exists"]` (substitute `<CURRENT_PROJECT_ROOT>`).
Otherwise: use `Q["project_root_first_time"]`.

**Handling answers:**
- "Keep current" / "保留現值" / "現在の値を保持" → use `skip`
- "Skip for now" / "稍後設定" / "後で設定する" → use `skip`
- "What is a project root?" / "什麼是專案根目錄？" / "プロジェクトルートとは？" → show the description inline, then ask Step 6 again
- User types in text field → use that text as the project root

---

## Step 7 — Proto Directory (if selected or first-time)

If `CURRENT_PROTO_DIR` exists: use `Q["proto_dir_exists"]` (substitute `<CURRENT_PROTO_DIR>`).
Otherwise: use `Q["proto_dir_first_time"]`.

**Handling answers:**
- "Keep current" / "保留現值" / "現在の値を保持" → use `skip`
- Option selected → use that value as-is
- User types in text field → use that text

---

## Step 8 — Map answers and save

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/save-config.sh" "<protoc_path or skip>" "<project_root or skip>" "<proto_dir or skip>" "<lang or skip>"
```

Stop after configuration is complete — do not proceed with the run flow.
