# earnings-reviewer — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `earnings-reviewer`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Post-earnings review for a covered name: read transcript + filings → update
coverage model → draft note. Cite:
`plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md` | 1-34 |
| CMA orchestrator manifest | `managed-agent-cookbooks/earnings-reviewer/agent.yaml` | 1-30 |
| Transcript-reader (UNTRUSTED) | `managed-agent-cookbooks/earnings-reviewer/subagents/transcript-reader.yaml` | 1-30 |
| Transcript-reader output schema | `managed-agent-cookbooks/earnings-reviewer/subagents/transcript-reader.yaml` | 17-30 |
| Model-updater subagent | `managed-agent-cookbooks/earnings-reviewer/subagents/model-updater.yaml` | 1-21 |
| Note-writer subagent (only Write) | `managed-agent-cookbooks/earnings-reviewer/subagents/note-writer.yaml` | 1-19 |
| Deploy + handoff notes | `managed-agent-cookbooks/earnings-reviewer/README.md` | 1-31 |

## Dependencies

- **MCP egress:** FactSet, Daloopa (read-only).
- **Skills:** `earnings-analysis`, `model-update`, `audit-xls`,
  `morning-note`, `earnings-preview`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **Highest Emerald relevance** of the 10 agents — covered-name post-earnings
   updates are a core Emerald Investment Advisors workflow.
2. **Transcript-reader injection risk** — transcripts are externally authored.
   Schema-validated output is the defense (`transcript-reader.yaml:17-30`).
3. **Consensus reproducibility gap** — FactSet consensus mutates over time;
   no archival of the consensus snapshot at draft time. V(A) reasonable-basis
   review requires Emerald to add a snapshot capture step.
4. **Coverage-model deltas need provenance** — `model-update` skill mutates
   the live coverage workbook; cell-by-cell source attribution is Emerald's
   responsibility (the skill labels but does not externally archive).
5. **"Never publish" guardrail at line 30** is prose-only.
6. **No Rule 204-2 hook** — earnings notes ARE published research per Reg AC
   if distributed; retention obligation applies the moment a draft becomes a
   published product.

## Compliance bucket

**(b)** — workable with hardening; the consensus-snapshot + 204-2 hooks are
Emerald-acute because outputs are research-product-class artifacts.

## Cross-references

- ARCHITECTURE.md §5
- EMERALD_ADAPTATION.md §earnings-reviewer
- PROMPTS_CATALOG.md §A.3, §B.3
