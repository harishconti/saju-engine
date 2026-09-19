# claude-context — Claude Code working memory for the saju engine

This directory holds the **Claude Code session artifacts** that produced the engine: the
persistent memory files and the raw conversation transcripts. They are checked in on purpose —
they are the provenance record for why the engine looks the way it does, and the audit trail
behind every decision in `docs/`.

## Layout

```
claude-context/
├── memory/                 Persistent memory files (loaded into context each session)
│   ├── MEMORY.md           Index — one line per memory
│   ├── engine-validation-campaign-2026-09.md
│   ├── saju-open-defects-triage.md
│   ├── climate-favorable-element-2026-09.md
│   ├── gtm-pivot-2026-09.md
│   ├── audit-2026-08-handoff.md
│   └── user-feedback-scope-decisions.md
└── sessions/               Raw session transcripts (.jsonl) + per-session subdirectories
```

## Provenance

| | |
|---|---|
| **Source directory** | `/home/harish/.claude/projects/-mnt-data2-git-repos-misc-saju/` |
| **Engine working tree** | `/mnt/data2/git_repos/misc/saju/` (not itself a git repository) |
| **Copied** | 2026-09-15 |
| **Method** | `rsync -a` (archival, no `--delete`) |

`memory/` is the authoritative copy that Claude Code reads. `sessions/` contains the
`.jsonl` transcripts for every session run against the engine tree, plus per-session
subdirectories holding subagent transcripts and tool results.

## What was excluded, and why

- **`auto-mode-classifier-error.txt`** (and any sibling of that filename). This is a Claude Code
  *harness diagnostic dump*, not engine context. It embeds Anthropic's internal auto-mode
  security-classifier system prompt verbatim (~160 KB) and, incidentally, echoes back the
  scanner regexes used to check it for credentials. Excluded for two independent reasons —
  it is internal security text rather than the user's own context, and it is the one artifact
  whose credential-match could not be fully characterized at copy time. Nothing the engine
  needs is lost by its absence.
- **Caches and build output**: `node_modules/`, `.next/`, `__pycache__/`, `.pytest_cache/`,
  `.ruff_cache/`, `.playwright-mcp/`, `venv/`, `*.pyc`, `*.deb`, `*.rpm`. These are
  reproducible and, in the case of `node_modules/`, hundreds of megabytes.

## Reading these files

The transcripts are newline-delimited JSON — one event per line — and are large (the largest
single file is ~40 MB). They are not meant to be read whole. To pull one specific thing out:

```bash
# every user turn in a session
jq -r 'select(.type=="user") | .message.content' \
  claude-context/sessions/<session-id>.jsonl | less

# search across all sessions without loading them
rg -n 'some phrase' claude-context/sessions/
```

## A note on scope

Nothing in this directory is imported, executed, or read by the engine at runtime. It is
documentation and history only. Deleting it breaks no tests.
