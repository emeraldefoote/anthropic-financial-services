# month-end-closer — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `month-end-closer`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Entity month-end close: accruals + roll-forwards + variance commentary →
close package staged for controller sign-off. Cite:
`plugins/agent-plugins/month-end-closer/agents/month-end-closer.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/month-end-closer/agents/month-end-closer.md` | 1-32 |
| CMA orchestrator manifest | `managed-agent-cookbooks/month-end-closer/agent.yaml` | 1-28 |
| Ledger-reader (UNTRUSTED — vendor invoices/statements) | `managed-agent-cookbooks/month-end-closer/subagents/ledger-reader.yaml` | 1-33 |
| Ledger-reader output schema | `managed-agent-cookbooks/month-end-closer/subagents/ledger-reader.yaml` | 17-33 |
| Rollforward subagent | `managed-agent-cookbooks/month-end-closer/subagents/rollforward.yaml` | 1-17 |
| Poster subagent (only Write) | `managed-agent-cookbooks/month-end-closer/subagents/poster.yaml` | 1-18 |
| Deploy notes + handoff from gl-reconciler | `managed-agent-cookbooks/month-end-closer/README.md` | 1-31 |

## Dependencies

- **MCP egress:** internal-gl (firm-internal). Same `GL_MCP_URL` env var
  as `gl-reconciler`'s GL MCP — coordinate the wiring.
- **Skills:** `accrual-schedule`, `roll-forward`, `variance-commentary`,
  `audit-xls`, `xlsx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **"No GL posting" invariant** — `month-end-closer.md:28` and
   `poster.yaml:7` both prohibit posting; agent stages JE drafts only.
   Emerald should add an enforcement test (per ARCHITECTURE.md §11.5).
2. **Vendor invoices/statements are externally authored** — ledger-reader
   is the untrusted-ingestion tier.
3. **Receives handoffs from `gl-reconciler`** — verified breaks fold into
   close commentary
   (`managed-agent-cookbooks/month-end-closer/README.md:31`).
4. **Medium Emerald relevance** — corporate accounting, applicable broadly.
5. **No Rule 204-2 hook** — close packages are operational records subject
   to general business-records retention plus any GAAP/audit retention
   Emerald is subject to.

## Compliance bucket

**(b)** — design is sound; hardening is the repo-wide three plus the
never-post invariant test.

## Cross-references

- ARCHITECTURE.md §11
- EMERALD_ADAPTATION.md §month-end-closer
- PROMPTS_CATALOG.md §A.9, §B.9
