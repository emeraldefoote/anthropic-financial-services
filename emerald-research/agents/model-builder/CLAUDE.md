# model-builder — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `model-builder`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Builds DCF / LBO / 3-statement / comps models live in Excel from a ticker +
assumption set. Cite:
`plugins/agent-plugins/model-builder/agents/model-builder.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/model-builder/agents/model-builder.md` | 1-34 |
| CMA orchestrator manifest | `managed-agent-cookbooks/model-builder/agent.yaml` | 1-30 |
| Data-puller subagent (MCP-only, schema-validated) | `managed-agent-cookbooks/model-builder/subagents/data-puller.yaml` | 1-30 |
| Builder subagent (only Write, Bash enabled) | `managed-agent-cookbooks/model-builder/subagents/builder.yaml` | 1-23 |
| Auditor subagent (re-check) | `managed-agent-cookbooks/model-builder/subagents/auditor.yaml` | 1-17 |
| dcf-model SKILL (Office JS branching) | `plugins/agent-plugins/model-builder/skills/dcf-model/SKILL.md` | 1-30 (header) |
| Deploy + handoff notes | `managed-agent-cookbooks/model-builder/README.md` | 1-31 |

## Dependencies

- **MCP egress:** CapIQ, Daloopa (read-only).
- **Skills:** `dcf-model`, `lbo-model`, `3-statement-model`, `comps-analysis`,
  `audit-xls`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **Bash enabled in `builder` subagent** (`builder.yaml:15`) — Python via
   bash for valuation calculations. **Sandbox attestation is a hard
   prerequisite for Emerald deployment** (no internet, no filesystem outside
   `./out/`, no subprocess to system Python with credential SDKs).
2. **No untrusted-document reader** — all inputs are MCP-vended; this is one
   of two agents (with `pitch-agent`) that skips the reader-isolation tier.
3. **Hardcoded-assumption provenance** — `model-builder.md:29` requires
   `[ASSUMPTION]` labels in cells, but no external assumption-set archive.
   V(A) reproducibility requires Emerald to capture (ticker, assumptions,
   model-type, model-file-hash, timestamp) tuples.
4. **Survivorship bias** in `comps-analysis` peer universe — same as
   `market-researcher` and `pitch-agent`.
5. **High Emerald relevance** — DCF + comps for ER side.
6. **Office JS vs openpyxl branching** in `dcf-model` SKILL.md — operative
   environment determines tooling choice (live Excel session vs headless
   `.xlsx`). Both paths require Emerald to verify the formulas-over-hardcodes
   discipline.

## Compliance bucket

**(b)** — Bash sandbox + assumption-archive + 204-2 + Cowork-prohibition are
the hardening line items; agent design itself is sound.

## Cross-references

- ARCHITECTURE.md §7
- EMERALD_ADAPTATION.md §model-builder
- PROMPTS_CATALOG.md §A.5, §B.5
