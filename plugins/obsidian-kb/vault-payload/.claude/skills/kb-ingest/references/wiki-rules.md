# Wiki Page Write Rules

## Creating New Pages

Use templates from `_schema/templates/`. Place files at:
```
wiki/entities/<name>.md
wiki/concepts/<name>.md
wiki/decisions/<decision-name>.md
wiki/troubleshooting/<problem-name>.md
wiki/sources/<YYYY-MM-DD>-<topic>.md
```

## Frontmatter Rules

- `status`: single source → `draft`; corroborated by multiple sources → `verified`
- `confidence`: direct statement → `high`; inferred → `medium`
- `provenance`: directly extracted → `extracted`; inferred → `inferred`
- `sources`: include session_id, date, project (cwd); if transcript path is known, also add `transcript:` field

## Transcript Reference for New Sessions

Each non-trivial new session should have a transcript. The ingest flow generates it via `upsert_transcripts.py` (step 4.5). When adding sources frontmatter, include the transcript wikilink once it exists.

## Wikilink Syntax in Page Content

When page content **describes or documents** `[[wikilink]]` syntax as an example (not as an actual cross-reference), always use one of these forms to avoid kb-lint false positives:

- Fenced code block: ` ```\n[[page-name]]\n``` `
- Escaped notation: `\[\[page-name\]\]`

Never write a bare `[[...]]` in prose or inline code spans if it doesn't refer to a real wiki page — kb-lint will flag it as a broken link.

## Updating Existing Pages

When updating an existing page:
1. Read the current content
2. Compare new information against existing content
3. **If a contradiction is found**:
   - Change frontmatter `status` to `contradicted`
   - Add a callout in the page body:
     ```
     > [!warning] 矛盾
     > 新來源（session: <id>，日期：<date>）與既有內容衝突：
     > - 既有：<old statement>
     > - 新來源：<new statement>
     > 待確認後更新。
     ```
   - Append new source to frontmatter `sources`
4. **If no contradiction**: merge updates, append source, upgrade status to `verified` if multiple sources
