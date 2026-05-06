# market-researcher — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `market-researcher`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Sector or thematic primer: industry overview + competitive landscape + peer
comps spread + ideas shortlist → research note (and optional deck). Cite:
`plugins/agent-plugins/market-researcher/agents/market-researcher.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/market-researcher/agents/market-researcher.md` | 1-37 |
| CMA orchestrator manifest | `managed-agent-cookbooks/market-researcher/agent.yaml` | 1-30 |
| Sector-reader (UNTRUSTED ingestion) | `managed-agent-cookbooks/market-researcher/subagents/sector-reader.yaml` | 1-32 |
| Sector-reader output schema | `managed-agent-cookbooks/market-researcher/subagents/sector-reader.yaml` | 17-32 |
| Comps-spreader subagent | `managed-agent-cookbooks/market-researcher/subagents/comps-spreader.yaml` | 1-20 |
| Note-writer subagent (only Write) | `managed-agent-cookbooks/market-researcher/subagents/note-writer.yaml` | 1-19 |
| Cowork plugin manifest | `plugins/agent-plugins/market-researcher/.claude-plugin/plugin.json` | 1-9 |
| Deploy + handoff notes | `managed-agent-cookbooks/market-researcher/README.md` | 1-31 |

## Dependencies

- **MCP egress:** CapIQ, FactSet (read-only).
- **Skills:** `sector-overview`, `competitive-analysis`, `comps-analysis`,
  `idea-generation`, `pptx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **Sector-reader is the highest prompt-injection-risk subagent** in the
   workflow — ingests third-party research PDFs and issuer materials. Defense
   pattern: schema-validated JSON output (`sector-reader.yaml:17-32`). Phase 4
   regression check mandatory.
2. **Idea-generation survivorship bias** — CapIQ/FactSet equity universe
   defaults to currently-listed names; ideas shortlist may exclude delisted
   underperformers. CFA V(A) flag.
3. **"8–15 names that define the space"** is operator-defined (`market-researcher.md:21`);
   universe-construction rule must be documented per V(A) reasonable basis.
4. **Cowork frontmatter declares `Write/Edit`** but CMA orchestrator strips it.
5. **No Rule 204-2 hook**.
6. **High Emerald relevance** — sector primers + ideas shortlists are core
   equity-research deliverables for Emerald Investment Advisors arm.

## Compliance bucket

**(b)** — repo-wide gaps + survivorship-bias hardening + sector-reader
injection-defense regression test required before production.

## Cross-references

- ARCHITECTURE.md §4
- EMERALD_ADAPTATION.md §market-researcher
- PROMPTS_CATALOG.md §A.2, §B.2
