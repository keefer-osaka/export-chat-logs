# Wiki Schema

這份文件定義知識庫的完整結構、操作流程與寫作規範。

---

## 目錄結構

```
wiki/
├── hot.md              # Hot cache：近期重要上下文（~500 字，vault 內啟動時自動注入）
├── index.md            # 主索引：所有頁面按類別列出
├── log.md              # 操作日誌：ingest 紀錄（只增不改）
├── overview.md         # 全局摘要：知識庫整體狀態
├── entities/           # 工具、框架、服務、人物
│   └── _index.md
├── concepts/           # 模式、架構、方法論
│   └── _index.md
├── decisions/          # 技術決策與理由
│   └── _index.md
├── troubleshooting/    # 問題與解法
│   └── _index.md
├── sources/            # 每個 session 的摘要
│   └── _index.md
└── meta/               # Lint 報告、統計
```

---

## 頁面類型

### entity（實體）
工具、框架、服務、人物、專案。

範例：`wiki/entities/rtk.md`、`wiki/entities/qmd.md`

### concept（概念）
模式、架構、方法論、設計原則。

範例：`wiki/concepts/hot-cache-pattern.md`、`wiki/concepts/three-layer-architecture.md`

### decision（決策）
技術選型、架構決策、與理由。

範例：`wiki/decisions/adopt-claude-obsidian-structure.md`

### troubleshooting（問題排查）
遇到的問題、症狀、解法、根本原因。

範例：`wiki/troubleshooting/jsonl-parse-error.md`

### source（來源摘要）
每個有價值的 session 的摘要，作為原始紀錄的索引。

範例：`wiki/sources/2026-04-11-obsidian-kb-planning.md`

---

## Frontmatter 規範

```yaml
---
title: 頁面標題
type: entity | concept | decision | troubleshooting | source
tags: [相關標籤]
status: draft | verified | stale | contradicted
confidence: high | medium | low
provenance: extracted | inferred | uncertain
sources:
  - session: <session-id>
    date: YYYY-MM-DD
    project: <cwd>
    transcript: "[[YYYY-MM-DD-<session-8chars>-<slug>]]"  # 由 kb-ingest 自動填入
transcripts:                                               # 頂層 list，Obsidian Properties 可點擊
  - "[[YYYY-MM-DD-<session-8chars>-<slug>]]"
created: YYYY-MM-DD
updated: YYYY-MM-DD
# 選填：壓制特定 lint 檢查（用於已知誤報）
lint_ignore:
  - canonical_drift   # 可選值：canonical_drift
---
```

### 欄位說明

**transcripts**（頂層 list）
- `sources[*].transcript` — 巢狀欄位，供機器讀取，記錄每個 source 條目對應的 transcript
- `transcripts:` — 頂層 list，供 Obsidian Properties 面板渲染為可點擊連結（Obsidian 不渲染巢狀物件內的 wikilink）
- 兩者由 `kb-ingest` 自動同步維護

**status**
- `draft` — 初稿，單一來源，未驗證
- `verified` — 多來源佐證，可信
- `stale` — 超過 90 天未更新，需重新驗證
- `contradicted` — 發現矛盾，需人工確認

**confidence**
- `high` — 直接從對話提取，明確無歧義
- `medium` — 有一定推論成分
- `low` — 不確定，待驗證

**provenance**
- `extracted` — 直接從對話文字提取
- `inferred` — 從上下文推論得出
- `uncertain` — 來源不清楚或模糊

**lint_ignore**（選填）
- 壓制特定 lint 檢查，用於已知誤報
- 目前支援值：`canonical_drift`、`stale`
- 範例：`lint_ignore: [canonical_drift, stale]`

---

## Callout 類型

### 矛盾標記
```
> [!warning] 矛盾
> 新來源（session: xxx）與既有內容衝突：
> - 既有：XXX
> - 新來源：YYY
> 待確認後更新。
```

### 知識缺口
```
> [!question] 知識缺口
> 這裡有不確定的部分，需要更多資訊。
```

### 關鍵洞見
```
> [!tip] 關鍵洞見
> 重要的發現或最佳實踐。
```

### 過時警告
```
> [!caution] 過時
> 此頁面超過 90 天未更新（最後更新：YYYY-MM-DD）。
```

---

## 操作流程

### INGEST（擷取）
執行 `/kb-ingest`：
1. 讀取水位線 `_schema/.watermark`
2. 掃描新的 JSONL session
3. 過濾瑣碎 session（output_tokens < 100 且 duration < 60s）
4. 提取 text blocks，忽略 tool_use
5. 判斷：建立新頁面 / 更新既有頁面 / 跳過
6. 矛盾檢測：若更新既有頁面發現衝突，標記 `status: contradicted`
7. 更新 `wiki/index.md`、`wiki/hot.md`、`wiki/log.md`
8. 更新水位線

### QUERY（查詢）

三段式漸進式揭露，大多數查詢在第 1 或 2 階段就能結束：

1. **優先 `wiki/hot.md`**：近期重要上下文（~500 字，在此 vault 目錄啟動時已自動注入），能回答就停止
2. **Stage 1 — Chunk 搜尋**：對具體問題使用 `qmd search "<q>"` 或 MCP `query` 工具，取得 top-5 chunks（各頁面的 `## TL;DR` 段為獨立高密度 chunk，BM25 優先命中）
3. **Stage 2 — TL;DR 確認**：chunk 命中後讀對應頁面的 `## TL;DR` 段（2-3 句），確認相關性；能回答就停止
4. **Stage 3 — 全頁讀取**：僅對最終確認相關的頁面執行 `Read`（完整內容）
5. **fallback**：qmd 無命中 → 讀 `wiki/index.md` 手動導航

### LINT（檢查）
執行 `/kb-lint`，輸出到 `wiki/meta/lint-report.md`：
- 孤立頁面（無 wikilink 指向）
- 斷裂連結（wikilink 指向不存在的頁面）
- 過時內容（status: stale）
- 重複頁面（標題或內容高度重疊）
- 矛盾未解（status: contradicted 超過 30 天）
- 無來源（sources 欄位為空）
- 低信心（confidence: low 且無後續佐證）
- 索引缺漏（存在於 wiki/ 但未列入 _index.md）

### SAVE（儲存）
Ingest 結束後自動執行：
- 更新 `wiki/hot.md`（保持 ~500 字）
- 追加 `wiki/log.md`
- 更新各子目錄 `_index.md`

---

## 命名慣例

- 檔名：小寫 kebab-case（e.g., `hot-cache-pattern.md`）
- 日期前綴（source 類型）：`YYYY-MM-DD-topic.md`
- Wikilink：`[[頁面標題]]` 或 `[[檔名]]`

---

## 寫作風格

- 繁體中文（台灣）
- 事實陳述，避免口語
- 每頁聚焦單一主題
- 保持簡潔：entity/concept 頁面 < 500 字
- source 頁面只保留關鍵決策與洞見，不逐字紀錄
