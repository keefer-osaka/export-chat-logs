---
name: auto
description: "Generate a launchd plist for automated weekly chat log exports on macOS. Use when user says 'auto export', 'automate export', 'set up launchd', 'weekly export', or 'schedule export'."
allowed-tools:
  - Bash
  - Read
  - AskUserQuestion
disable-model-invocation: true
---

# Schedule Automated Chat Log Export

**Silent mode:** Do not print any text between steps — this includes step names, headers, or labels (e.g. do NOT output "Step 7" or any step identifier). Proceed directly from one step to the next without outputting status messages, summaries, or confirmations. Only allowed outputs: (1) the Telegram-not-configured error, (2) AskUserQuestion calls, (3) the script's stdout (Step 6).

## Step 1 — Read current config

Read `~/.config/devtools-plugins/export-chat-logs/.env` (use `$HOME` if `~` doesn't work).

Extract:
- `CURRENT_TOKEN` (present if set)
- `CURRENT_CHAT_ID` (present if set)
- `CURRENT_LANG` (default: `en`)
- `CURRENT_TZ` (timezone offset as integer, e.g. `9` for UTC+9; default: `8`)

**If `CURRENT_TOKEN` or `CURRENT_CHAT_ID` is empty or the file does not exist:**
Stop and print (EN/ZH-TW/JA trilingual):

> ⚠️ Telegram is not configured. Run `/export-chat-logs:setup` first, then re-run `/export-chat-logs:auto`.
> ⚠️ Telegram 尚未設定。請先執行 `/export-chat-logs:setup`，再重新執行 `/export-chat-logs:auto`。
> ⚠️ Telegram が設定されていません。先に `/export-chat-logs:setup` を実行してから `/export-chat-logs:auto` を再実行してください。

---

## Step 2 — Determine language (`SETUP_LANG`)

`SETUP_LANG = CURRENT_LANG`

Read `"${CLAUDE_PLUGIN_ROOT}/skills/auto/questions/${SETUP_LANG}.json"`, store as `Q`.

---

## Step 3 — Ask schedule time

Default suggestion is Monday 17:00 local time:
- `SUGGESTED_WEEKDAY` = 1, `SUGGESTED_HOUR` = 17, `SUGGESTED_MINUTE` = 0
- `SUGGESTED_LOCAL` = EN: `"Every Monday at 5pm"` / ZH-TW: `"每週一下午五點"` / JA: `"毎週月曜日の午後5時"`

Substitute `<SUGGESTED_TIME>` in `Q["schedule_time"]` with `SUGGESTED_LOCAL`, then use AskUserQuestion.

**Handling answers:**
- Recommended option selected → `FINAL_WEEKDAY = 1`, `FINAL_HOUR = 17`, `FINAL_MINUTE = 0`
- `"Custom time"` / `"自訂時間"` / `"カスタム時間"` selected → wait for text field input
- Text field input:
  - If it looks like a cron expression (5 space-separated fields, e.g. `30 23 * * 0`) → extract minute, hour, day-of-week fields; treat as local time
  - Otherwise parse as natural language (e.g. `"every Sunday at 10:30pm"`, `"每週日晚上十點半"`, `"毎週日曜日の夜10時半"`) → extract weekday, hour, minute as local time

Store as `FINAL_WEEKDAY`, `FINAL_HOUR`, `FINAL_MINUTE`.

---

## Step 4 — Ask export days

Use `Q["export_days"]` with AskUserQuestion.

**Handling answers:**
- `"7 days (Recommended)"` / `"7 天（建議）"` / `"7 日間（推奨）"` → `DAYS=7`
- `"14 days"` / `"14 天"` / `"14 日間"` → `DAYS=14`
- `"30 days"` / `"30 天"` / `"30 日間"` → `DAYS=30`
- Text field input (number) → `DAYS=<number>`

---

## Step 5 — Ask plugin scope

Use `Q["plugin_scope"]` with AskUserQuestion.

**Handling answers:**
- `"User scope (Recommended)"` / `"使用者範圍（建議）"` / `"ユーザースコープ（推奨）"` → `PROJECT_DIR=""`, `PLUGIN_DIR_PATH=""`
- `"Project scope"` / `"專案範圍"` / `"プロジェクトスコープ"` → text field input is `PROJECT_DIR` (absolute path); `PLUGIN_DIR_PATH=""`
- `"Local dev (git clone)"` / `"本機開發（git clone）"` / `"ローカル開発（git clone）"` → text field input is `PLUGIN_DIR_PATH` (absolute path to plugin dir, e.g. `/path/to/devtools-plugins/plugins/export-chat-logs`); `PROJECT_DIR=""`

---

## Step 6 — Install launchd agent

Run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/install-launchd.sh" \
  "$FINAL_WEEKDAY" "$FINAL_HOUR" "$FINAL_MINUTE" \
  "$DAYS" "${PROJECT_DIR:-skip}" "${PLUGIN_DIR_PATH:-skip}" "$SETUP_LANG"
```

The script handles everything: plist generation, `launchctl` load, summary markdown file, and success message. Print the script's output as-is. No further output needed.
