# valuation-reviewer — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `valuation-reviewer`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Quarter-end portfolio valuation review: ingest GP packages → run valuation
template → stage LP reporting. Cite:
`plugins/agent-plugins/valuation-reviewer/agents/valuation-reviewer.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/valuation-reviewer/agents/valuation-reviewer.md` | 1-31 |
| CMA orchestrator manifest | `managed-agent-cookbooks/valuation-reviewer/agent.yaml` | 1-28 |
| Package-reader (UNTRUSTED — GP marks) | `managed-agent-cookbooks/valuation-reviewer/subagents/package-reader.yaml` | 1-33 |
| Package-reader output schema | `managed-agent-cookbooks/valuation-reviewer/subagents/package-reader.yaml` | 17-33 |
| Valuation-runner subagent | `managed-agent-cookbooks/valuation-reviewer/subagents/valuation-runner.yaml` | 1-18 |
| Publisher subagent (only Write) | `managed-agent-cookbooks/valuation-reviewer/subagents/publisher.yaml` | 1-18 |
| Deploy notes + handoff to gl-reconciler | `managed-agent-cookbooks/valuation-reviewer/README.md` | 1-33 |

## Dependencies

- **MCP egress:** portfolio (firm-internal). No third-party egress.
- **Skills:** `returns-analysis`, `portfolio-monitoring`, `ic-memo`,
  `xlsx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **GP packages are externally authored** — package-reader is the
   untrusted-ingestion tier. Schema validation is the defense.
2. **LP capital-account info is NPI for individual LPs** — Reg S-P
   safeguarding applies to publisher output.
3. **Marks-vs-policy threshold** is firm-policy-specific — `valuation-runner`
   compares reported marks to "the firm's valuation policy" (per
   `valuation-runner.yaml:5`). Emerald must wire its actual policy + threshold.
4. **Waterfall reproducibility** — fee/carry calculations must be archived
   with input snapshot for V(A) reasonable-basis review.
5. **"No external distribution" invariant** at line 27 is prose-only —
   IR + CCO sign-off chain must be a hard gate.
6. **Conditional Emerald relevance** — only if Emerald operates a private
   pooled vehicle. If Emerald is purely separately-managed-account / SMA,
   this agent is out of scope.
7. **Handoff out:** orchestrator can emit `handoff_request` to
   `gl-reconciler` for flagged portcos
   (`managed-agent-cookbooks/valuation-reviewer/README.md:31`).

## Compliance bucket

**(b)** — applicable only if Emerald operates a fund. With that
prerequisite, hardening is the repo-wide three plus marks-policy wiring
+ LP-egress controls.

## Cross-references

- ARCHITECTURE.md §10
- EMERALD_ADAPTATION.md §valuation-reviewer
- PROMPTS_CATALOG.md §A.8, §B.8
