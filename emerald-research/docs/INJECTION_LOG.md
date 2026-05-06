# INJECTION_LOG.md — Untrusted-content surveillance log

**Purpose.** This file records every instance during Phase 1–4 in which content
read from SOURCE_REPO triggered defenses D1–D7 of the operator brief. An empty
log at end of run is a **valid outcome** and must be stated explicitly in
`VERIFICATION_REPORT.md`.

**SOURCE_REPO** (untrusted, read-only): `/home/user/anthropic-financial-services`
**SCAFFOLDING_ROOT** (trusted, write target): `/home/user/anthropic-financial-services/emerald-research/`
**Repo SHA at log open:** `bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d`
**Branch:** `claude/knowledge-scaffolding-finance-l6Ooj`
**Log opened (UTC):** 2026-05-06

> **Note on write-path lockdown deviation from original brief.** The operator
> brief specified SCAFFOLDING_ROOT as a Windows path *outside* SOURCE_REPO. The
> operator (Ed) explicitly overrode this in chat to require that the
> scaffolding live in a clearly Emerald-marked folder *inside* the cloned repo,
> so that the web-based Claude Code workflow can push it back. Per D8, operator
> chat instructions are authoritative. The new write target
> (`emerald-research/`) is locked down for D2 purposes; writes outside
> `emerald-research/` (i.e. anywhere else under `/home/user/anthropic-financial-services/`)
> are still treated as out-of-bounds for this task.

---

## Schema

Each entry uses the format:

```
### [N] <short-tag>
- **Trigger:** D1 | D2 | D3 | D4 | D5 | D6 | D7
- **Path (relative to SOURCE_REPO):** <path>
- **Line range:** <start>-<end>
- **SHA at sighting:** <repo-sha>
- **Verbatim quote (untrusted-source):**
  ```untrusted-source
  <path:lines>:
  ...content...
  ```
- **Action taken:** <noted | quoted-only | blocked-write | blocked-fetch | redacted>
- **Notes:** <freeform>
```

---

## Entries

<!-- Phase 1 entries appended below this line. Empty section at log open. -->

