# Knowledge Classification Standards

Use these criteria when analyzing session messages to determine which knowledge is worth extracting.

## Categories

**entity** — Tools, frameworks, services worth recording:
- Mentioned a specific tool/package and discussed its purpose, installation, or configuration
- Examples: RTK, qmd, memsearch, specific npm packages, CLI tools

**concept** — Architecture, patterns, methodologies:
- Discussed a design pattern, the rationale behind an architectural decision
- Examples: hot cache pattern, three-tier knowledge base architecture, JSONL parsing approach

**decision** — Technical choices:
- Explicitly chose one approach over another, with justification
- Examples: choosing qmd as the search layer, adopting claude-obsidian directory structure

**troubleshooting** — Problems encountered and resolved:
- Error messages, debugging process, final solution
- Examples: sandbox permission issues, JSONL parse errors

**source** — Session summary (selective):
- Create a summary page only for sessions involving architecture discussion, important decisions, or complex problem-solving
- Do NOT create one for every session

## Skip Conditions

Skip a session (or parts of it) when:
- Pure small talk with no technical content
- Duplicate content already well-documented in wiki/
