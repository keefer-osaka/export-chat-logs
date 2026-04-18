# Claude Code 知識庫（Obsidian Vault）

這個 Obsidian vault 是 Claude Code 的**持久記憶系統**，讓 AI 在不同 session 之間保持知識連續性。

---

## 架構概覽

```
~/.claude/projects/**/*.jsonl      L1：全域對話歷史（自動寫入）
         ↓  /kb-ingest（手動）
transcripts/                        L1.5：對話歸檔層（清理後全文）
         ↓
wiki/                               L2：結構化知識 Wiki
         ↓  在此 vault 目錄啟動 Claude Code 時自動注入
CLAUDE.md → wiki/hot.md             L3：啟動上下文
```

### 三層記憶召回

| 層級        | 觸發方式             | 說明                                                                            |
| --------- | ---------------- | ----------------------------------------------------------------------------- |
| L3 hot.md | 自動（vault 內啟動）    | 工作目錄為此 vault 時，`CLAUDE.md` 引用 `wiki/hot.md` 自動注入近期上下文；其他專案目錄的 session 不會載入    |
| L2 語意     | 手動（`/obsidian-kb:search <問題>`） | 任何 session 輸入指令觸發 qmd 搜尋（skill 呼叫）                                  |

---

## 目錄結構

```
Obsidian/
├── CLAUDE.md           # L3 啟動注入（載入 hot.md、說明 vault 用途）
├── WIKI.md             # Wiki Schema 規範（頁面類型、frontmatter、操作流程）
├── README.md           # 本文件
├── wiki/
│   ├── hot.md          # Hot cache（~500 字，近期重要上下文）
│   ├── index.md        # 主索引（所有頁面按類別）
│   ├── log.md          # Ingest 操作日誌
│   ├── overview.md     # 知識庫全局摘要與統計
│   ├── entities/       # 工具、框架、服務
│   ├── concepts/       # 架構模式、方法論
│   ├── decisions/      # 技術決策與理由
│   ├── troubleshooting/# 問題與解法
│   ├── sources/        # 重要 Session 摘要
│   └── meta/           # Lint 報告、統計報告
├── transcripts/        # L1.5：對話歸檔（每個 session 一個 md 檔）
├── _schema/            # Sessions manifest、水位線、模板
│   ├── sessions.json   # 所有已處理 session 的索引
│   ├── .watermark      # 一般模式水位線（ISO 8601 時間戳）
│   ├── .all_watermark  # --all 模式獨立游標
│   └── templates/      # Wiki 頁面 frontmatter 模板
└── .claude/
    └── skills/
        ├── kb-ingest/  # 知識擷取 skill
        ├── kb-lint/    # 健康檢查 skill
        └── kb-stats/   # 統計報告 skill
```

---

## 可用 Skills

### `/kb-ingest` — 知識擷取

從 JSONL 對話歷史中擷取知識，寫入 wiki 頁面。

```
/kb-ingest             # 處理水位線之後的新 sessions（預設 10 筆）
/kb-ingest -a          # 批次處理所有歷史 sessions（預設每批 10 筆）
/kb-ingest --all       # 同上（長格式）
/kb-ingest -n 20       # 自訂每批數量（短格式，可與 -a / --all 合用）
/kb-ingest --limit 20  # 同上（長格式）
```

**執行流程**：
1. 掃描新 sessions（依水位線過濾）
2. 逐 session 分析，判斷知識類型（entity/concept/decision/troubleshooting/source）
3. 讀取現有 wiki 頁面，避免重複
4. 寫入或更新 wiki 頁面（矛盾偵測 → 加 callout 而非靜默覆蓋）
5. 建立 transcript 歸檔（L1.5）
6. 更新 `wiki/hot.md`、`wiki/log.md`、各 `_index.md`
7. 刷新 qmd 索引（`qmd update --collection obsidian-wiki`）
8. 推進水位線

**為什麼是手動？**  
/kb-ingest 需要 LLM 判斷：評估內容價值、決定建新頁或更新、偵測矛盾、撰寫結構化知識。這無法用純 shell hook 自動化（不同於 memsearch 的機械式 embedding）。

### `/kb-lint` — 健康檢查

掃描 wiki/，輸出 `wiki/meta/lint-report.md`，檢查：
- Canonical drift（頁面內容與標題不符）
- 斷裂連結（wikilink 指向不存在的頁面）
- 孤立頁面（無連結指向）
- 無來源頁面
- 矛盾未解（status: contradicted 超過 30 天）
- 索引缺漏
- 過時頁面（status: stale）

### `/kb-stats` — 統計報告

輸出 `wiki/meta/stats-report.md`，涵蓋：
- 頁面分佈（各類型數量）
- 狀態分佈（draft/verified/stale/contradicted）
- TL;DR 覆蓋率、來源覆蓋率、Transcript 連結率
- 新鮮度（30/60/90 天內更新比例）
- Transcripts 層統計

---

## 自動 vs 手動

| 操作 | 自動/手動 | 說明 |
|------|-----------|------|
| JSONL 寫入 | 自動 | Claude Code 每次對話結束自動寫入 |
| hot.md 注入 | 自動 | CLAUDE.md 引用，session 啟動時自動載入 |
| /kb-ingest | **手動** | 需要 LLM 判斷，無法自動化 |
| /kb-lint | 手動 | 定期執行或懷疑有問題時執行 |
| /kb-stats | 手動 | 想查看覆蓋率時執行 |

---

## 依賴項目

| 工具 | 版本 | 用途 |
|------|------|------|
| [qmd](https://github.com/tobil4sk/qmd) | v2.1.0+ | 本地 markdown 搜尋引擎（BM25+向量混合） |
| Python 3 | 3.9+ | Ingest 腳本、水位線管理 |
| Claude Code | 最新版 | Skill 執行環境 |

### qmd 安裝

```bash
bun install -g @tobilu/qmd
qmd init
qmd add collection obsidian-wiki /path/to/Obsidian/wiki
qmd update --collection obsidian-wiki
```

### Settings.json 沙盒白名單

qmd cache 路徑需加入 `~/.claude/settings.json` 的 `allowWrite`：

```json
{
  "sandbox": {
    "allowWrite": [
      "~/.cache/qmd"
    ]
  }
}
```

修改後需重開 session 才生效。

---

## Wiki 頁面規範

詳見 `WIKI.md`，重點：

- **繁體中文（台灣）**撰寫
- 每頁聚焦單一主題，entity/concept < 500 字
- Frontmatter 必填：`title`、`type`、`status`、`confidence`、`provenance`、`sources`
- `status` 進階路徑：`draft` → `verified`（多來源佐證）/ `contradicted`（發現矛盾）/ `stale`（90天未更新）
- 矛盾不靜默覆蓋，加 `[!warning]` callout 等待人工確認

---

## 設計原則

1. **單一來源原則**：此 vault 是唯一的持久記憶，不與其他記憶系統（如 `~/.claude/.../memory/`）並存
2. **品質重於數量**：一個 session 通常只產生 1-3 個有價值頁面，不強行分類
3. **矛盾標記而非覆蓋**：知識有衝突時標記待確認，不靜默丟棄舊知識
4. **漸進式揭露**：hot.md（500字）→ qmd chunk → TL;DR → 全頁讀取，大多數查詢在前兩步就能結束

---

## 參考

- [Andrej Karpathy - LLM Wiki 模式](https://x.com/karpathy)（三層架構靈感來源）
- [claude-obsidian](https://github.com/nicholaswmin/claude-obsidian)（358 stars，wiki 結構借鑑來源）
- [obsidian-wiki by Ar9av](https://github.com/Ar9av/obsidian-wiki)（282 stars，ingest pipeline 參考）
- [qmd by Tobi Lütke](https://github.com/tobil4sk/qmd)（本地搜尋引擎）
