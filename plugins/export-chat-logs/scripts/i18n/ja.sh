# 日本語 locale strings for shell scripts (upload.sh, save-config.sh)

# upload.sh - error / warning
ERR_NOT_CONFIGURED="❌ 未設定です。実行してください：/export-chat-logs:setup"
ERR_TOKEN_EMPTY="❌ Telegram Bot Token が空です。実行してください：/export-chat-logs:setup"
ERR_CHATID_EMPTY="❌ Telegram chat_id が空です。実行してください：/export-chat-logs:setup"
WARN_NO_SESSIONS="⚠️  過去 %DAYS% 日間にセッションが見つかりませんでした。スキップします。"

# upload.sh - summary text (Telegram message)
SUMMARY_HEADER="📦 チャットログエクスポート"
SUMMARY_USER="👤 ユーザー：%GIT_USER%"
SUMMARY_PERIOD="📅 期間：%START_DATE% ~ %TODAY%（過去 %DAYS% 日間）"
SUMMARY_STATS="📊 統計：%CC_SESSIONS% セッション"
SUMMARY_SIZE="💾 ファイルサイズ：%ZIP_SIZE%"
SUMMARY_FORMAT_HTML="📝 形式：HTML（シンタックスハイライト + インタラクティブグラフ）"
SUMMARY_FORMAT_MD="📝 形式：Markdown（ツール呼び出しと技術的詳細は省略）"
MSG_DONE="✅ 完了！Claude Code：%CC_SESSIONS% セッション、zip：%ZIP_SIZE%、Telegram に送信済み"
STATS_REPORT_SLUG="claude-code_使用レポート"
STATS_REPORT_SLUG_COWORK="claude-cowork_使用レポート"

# Cowork
SUMMARY_STATS_COWORK="📊 統計：%CC_SESSIONS% セッション（Claude Code）+ %CW_SESSIONS% セッション（Claude Cowork）"
MSG_DONE_COWORK="✅ 完了！Claude Code：%CC_SESSIONS% セッション、Claude Cowork：%CW_SESSIONS% セッション、zip：%ZIP_SIZE%、Telegram に送信済み"

# save-config.sh
ERR_TOKEN_REQUIRED="❌ Token が必要です：bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
ERR_CHATID_REQUIRED="❌ Chat ID が必要です：bash save-config.sh <token> <chat_id> [timezone] [lang] [format]"
MSG_CONFIG_SAVED="✅ 設定を保存しました（Token + Chat ID + タイムゾーン %TZ_LABEL% + 言語 %LANG% + 形式 %FORMAT% + Cowork %COWORK%）"
