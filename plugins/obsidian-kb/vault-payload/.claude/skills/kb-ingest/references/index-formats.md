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
