---
name: kb-stats
description: 知識庫統計報告。掃描 wiki/ 輸出頁面分佈、狀態、新鮮度、來源覆蓋率、Transcripts 層狀態。
usage: /kb-stats
---

# kb-stats

執行知識庫統計，輸出報告到 `wiki/meta/stats-report.md`。

## 執行方式

```bash
python3 __VAULT_DIR__/.claude/skills/kb-stats/scripts/stats_wiki.py
```

## 統計項目

| # | 名稱 | 說明 |
|---|------|------|
| 1 | 頁面分佈 | 各類型（entity/concept/decision/troubleshooting/source）頁面數 |
| 2 | 狀態分佈 | draft / verified / stale / contradicted 各佔比 |
| 3 | 信心度分佈 | high / medium / low 各佔比 |
| 4 | TL;DR 覆蓋率 | 有 `## TL;DR` 段落的頁面比例 |
| 5 | 來源覆蓋率 | 有 sources 欄位的頁面比例、平均來源數 |
| 6 | Transcript 連結率 | sources 條目中有 transcript: 欄位的比例 |
| 7 | 新鮮度 | 30/60/90 天內更新的頁面數、最舊頁面 |
| 8 | Transcripts 層 | transcripts/ 總數、sessions.json 條目數 |

## 輸出

- `wiki/meta/stats-report.md` — 完整報告
- stdout — 同上（供即時查看）
