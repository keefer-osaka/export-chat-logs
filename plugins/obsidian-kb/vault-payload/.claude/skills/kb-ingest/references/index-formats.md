# Index File Update Formats

## wiki/\<subdir\>/_index.md

Append a new entry for each new page in the corresponding subdirectory:
```markdown
- [[Page Title]] — one-sentence description
```

## wiki/index.md

Verify that links to each subdirectory's `_index.md` exist (usually no changes needed).

## wiki/hot.md

Update the hot cache, keeping it to ~500 words. Content should reflect the most recent ingest highlights:
- Topics of recently processed sessions
- Key new knowledge points from recent ingests (2–3 items per category)
- Most important entities/concepts currently in the knowledge base

## wiki/log.md

Append an entry for this ingest run:
```markdown
## <YYYY-MM-DD HH:MM>
- 處理 sessions：N 個
- 新增頁面：N 個（entity: N, concept: N, decision: N, troubleshooting: N, source: N）
- 更新頁面：N 個
- 跳過：N 個
- 矛盾標記：N 個
- 水位線：<timestamp>
```

## wiki/overview.md

知識庫全局摘要，由 `update_overview.py` + LLM 混合維護：

**機械段（腳本自動覆寫）**
- `## 狀態`：初始化日期、總頁面數（按類型）、最後 ingest、水位線、Transcripts 計數

**敘事段（LLM 維護，腳本不觸碰）**
- `## 主要主題`：知識庫的主要領域，長期有效，重大轉向時更新
- `## 近期重點`：最近 3–5 次 ingest 的重點，每次 ingest append 一條

**靜態段（永不更動）**
- `## 架構說明`：三層架構說明
- `## 安裝資訊`：plugin 安裝記錄
