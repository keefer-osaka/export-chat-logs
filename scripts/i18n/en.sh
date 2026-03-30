# English locale strings for shell scripts (export.sh, setup.sh, save-token.sh)

# export.sh - error / warning
ERR_NOT_CONFIGURED="❌ Not configured. Please run: /export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token is empty. Please run: /export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id is empty. Please run: /export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  No sessions found in the last %DAYS% days, skipping."

# export.sh - summary text (Telegram message)
SUMMARY_HEADER="📦 Chat Log Export"
SUMMARY_USER="👤 User: %GIT_USER%"
SUMMARY_PERIOD="📅 Period: %START_DATE% ~ %TODAY% (last %DAYS% days)"
SUMMARY_STATS="📊 Stats: %CC_SESSIONS% sessions"
SUMMARY_SIZE="💾 File size: %ZIP_SIZE%"
SUMMARY_FORMAT_HTML="📝 Format: HTML (syntax highlighting + interactive charts)"
SUMMARY_FORMAT_MD="📝 Format: Markdown (tool calls and technical details omitted)"
MSG_DONE="✅ Done! Claude Code: %CC_SESSIONS% sessions, zip: %ZIP_SIZE%, sent to Telegram"
STATS_REPORT_SLUG="claude-code_stats-report"

# save-token.sh
ERR_TOKEN_REQUIRED="❌ Token required: bash save-token.sh <token> <chat_id> [timezone] [lang] [format]"
ERR_CHATID_REQUIRED="❌ Chat ID required: bash save-token.sh <token> <chat_id> [timezone] [lang] [format]"
MSG_CONFIG_SAVED="✅ Configuration saved (Token + Chat ID + Timezone %TZ_LABEL% + Language %LANG% + Format %FORMAT%)"

# setup.sh - labels
LABEL_BOT_TOKEN_SET="Bot Token: %VALUE%"
LABEL_BOT_TOKEN_UNSET="Bot Token: (not set)"
LABEL_CHAT_ID_SET="Chat ID: %VALUE%"
LABEL_CHAT_ID_UNSET="Chat ID: (not set)"
LABEL_TIMEZONE_SET="Timezone: %VALUE%"
LABEL_TIMEZONE_UNSET="Timezone: (not set, default UTC+8)"
LABEL_LANG_SET="Language: %VALUE%"
LABEL_LANG_UNSET="Language: (not set, default en)"
LABEL_FORMAT_SET="Output Format: %VALUE%"
LABEL_FORMAT_UNSET="Output Format: (not set, default html)"
