# export-chat-logs

Claude Code plugin — 收集 Claude Code 聊天記錄，轉換為 HTML 或 Markdown 格式，打包成 zip，並透過 Telegram 傳送。

[English](README.md)

## 安裝

### 方式一：`claude --plugin-dir`（本機開發 / 快速測試）

```bash
git clone https://github.com/keefer-osaka/devtools-plugins.git /path/to/devtools-plugins
claude --plugin-dir /path/to/devtools-plugins
```

### 方式二：透過 plugin marketplace

```
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install export-chat-logs@devtools-plugins
```

安裝後請**重新啟動 Claude Code**，才能看到 `/export-chat-logs:setup` 和 `/export-chat-logs:upload` 指令。`/reload-plugins` 無法載入新安裝的 skill。

### 解除安裝

```
/plugin uninstall export-chat-logs@devtools-plugins
/reload-plugins
```

移除 marketplace 來源：

```
/plugin marketplace remove devtools-plugins
```

---

## 初始設定

安裝後，執行以下指令設定 Telegram Bot Token、chat_id 和時區：

```
/export-chat-logs:setup
```

依提示輸入：
- **Bot Token**：在 Telegram 找到 `@BotFather` → `/mybots` → 選擇你的 bot → API Token
- **Chat ID**：在 Telegram 找到 `@userinfobot`，傳送任意訊息，它會回覆你的 chat_id
- **時區偏移**：整數，例如 `8`（UTC+8，台灣）、`9`（UTC+9，日本）、`-5`（UTC-5，EST）；預設為 `8`
- **語言**：`en`（英文）或 `zh-TW`（繁體中文）；預設為 `en`
- **輸出格式**：`html`（語法高亮 + 互動式圖表）或 `md`（純 Markdown）；預設為 `html`

設定儲存於 `~/.config/devtools-plugins/export-chat-logs/.env`（權限 600，不納入 repo）。

如需修改單一設定，重新執行 `/export-chat-logs:setup`，不想更改的欄位輸入 `skip` 保留現有值。

---

## 使用方式

### 匯出（預設 7 天）

```
/export-chat-logs:upload
```

### 指定天數

```
/export-chat-logs:upload 14
```

### 非互動模式（`claude -p`）

```bash
claude -p "upload chat logs" --allowedTools "Bash,Read"
claude -p "upload chat logs 14" --allowedTools "Bash,Read"
```

---

## 環境需求

- macOS（Linux 需調整 `date` 指令）
- Python 3
- `curl`、`zip`
- Claude Code CLI

---

## 匯出內容

- Claude Code：來自 `~/.claude/projects/` 的 JSONL 對話記錄
- 每個對話轉換為一個 HTML 檔案（或 Markdown，依設定而定）
- HTML 包含語法高亮（highlight.js）與互動式圖表（Mermaid.js）
- 包含統計報告（對話數、模型用量、分類統計）
- 打包成 zip 並傳送至 Telegram

---

## 疑難排解

### `git pull` 後 plugin 沒有更新

marketplace 會在本機快取特定版本。若拉取後變更未反映，請清除快取並重新安裝：

```bash
rm -rf ~/.claude/plugins/cache/devtools-plugins
```

在 Claude Code 中重新安裝：

```
/plugin marketplace remove devtools-plugins
/plugin marketplace add keefer-osaka/devtools-plugins
/plugin install export-chat-logs@devtools-plugins
```

重新安裝後重啟 Claude Code。

---

## 檔案結構

```
.claude-plugin/
└── plugin.json             # Plugin 元資料
skills/
├── upload/SKILL.md         # /export-chat-logs:upload
└── setup/SKILL.md          # /export-chat-logs:setup
scripts/
├── common.py               # 共用邏輯（JSONL 解析、i18n/tz 載入）
├── export.sh               # 主匯出流程
├── setup.sh                # 顯示目前設定狀態
├── save-token.sh           # 寫入 token + chat_id + 時區 + 語言 + 格式
├── convert_to_html.py      # JSONL → HTML（語法高亮 + 圖表）
├── convert_to_markdown.py  # JSONL → Markdown
├── generate_stats.py       # 統計報告（HTML 或 Markdown）
└── i18n/                   # 多語言字串
    ├── en.sh / en.py           # 英文
    └── zh_TW.sh / zh_TW.py    # 繁體中文
```
