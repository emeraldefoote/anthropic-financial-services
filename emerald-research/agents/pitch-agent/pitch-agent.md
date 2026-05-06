# pitch-agent — Emerald research mirror

> **Untrusted-source notice.** This is an Emerald-internal mirror for the
> `pitch-agent` shipped in SOURCE_REPO. It is generated and lives outside
> SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

End-to-end IB pitch agent: target + situation → trading comps + precedents +
DCF + LBO + football field → branded pitch deck. Cite:
`plugins/agent-plugins/pitch-agent/agents/pitch-agent.md:3`.

## Key SOURCE_REPO files (with line-range pointers to critical logic)

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/pitch-agent/agents/pitch-agent.md` | 1-36 |
| Cowork plugin manifest | `plugins/agent-plugins/pitch-agent/.claude-plugin/plugin.json` | 1-9 |
| CMA orchestrator manifest | `managed-agent-cookbooks/pitch-agent/agent.yaml` | 1-30 |
| Read-only orchestrator toolset | `managed-agent-cookbooks/pitch-agent/agent.yaml` | 10-19 |
| Researcher subagent (MCP-only) | `managed-agent-cookbooks/pitch-agent/subagents/researcher.yaml` | 1-47 |
| Modeler subagent (Bash + MCPs) | `managed-agent-cookbooks/pitch-agent/subagents/modeler.yaml` | 1-23 |
| Deck-writer subagent (only Write) | `managed-agent-cookbooks/pitch-agent/subagents/deck-writer.yaml` | 1-20 |
| Deploy + handoff notes | `managed-agent-cookbooks/pitch-agent/README.md` | 1-31 |
| Steering examples | `managed-agent-cookbooks/pitch-agent/steering-examples.json` | full file |

## Dependencies

- **MCP egress:** CapIQ, Daloopa (read-only). Cite `agent.yaml:17-22`.
- **Skills bundled:** `sector-overview`, `comps-analysis`, `lbo-model`,
  `dcf-model`, `3-statement-model`, `audit-xls`, `pitch-deck`, `ib-check-deck`,
  `deck-refresh` — vendored from `plugins/vertical-plugins/{financial-analysis,
  investment-banking,equity-research}/skills/<name>/` per `scripts/sync-agent-skills.py`.
- **Model:** `claude-opus-4-7` (orchestrator + all 3 subagents).
- **No firm-internal MCPs** — all data egress is to public-market vendors.

## Known gotchas (from Phase 2)

1. **Cowork frontmatter declares `Write/Edit`** (`pitch-agent.md:4`) but the
   CMA orchestrator strips Write (`agent.yaml:14-16`). For Emerald (CMA-only),
   the orchestrator is read-only. Do not rely on the Cowork-mode permission
   set when planning hardening.
2. **`modeler` subagent has Bash enabled** (`modeler.yaml:14`). Sandbox
   attestation required before any Emerald deployment — see
   `../../docs/EMERALD_ADAPTATION.md` §pitch-agent for required sandbox rules.
3. **Survivorship bias risk** in `comps-analysis` peer universe (CapIQ default
   includes only currently-listed names). CFA V(A) flag.
4. **No Rule 204-2 hook** — outputs land in `./out/` with deterministic names
   (`pitch-<target>.pptx`, `model.xlsx`) but no audit-trail capture.
5. **"Stop and surface for review" guardrail** at `pitch-agent.md:32` is
   prose-only; not enforced by any tool gate.
6. **Out of Emerald mandate** — RIA does not produce IB pitches. This agent
   is documented but not slated for Emerald deployment.

## Compliance bucket

**(b)** — requires Emerald hardening before production use.

Per ARCHITECTURE.md §3.5: workflow itself is sound; bucket assignment is
driven by repo-wide gaps (Cowork primacy, no 204-2 hook, no §204A audit
trail). Out-of-mandate caveat noted above.

## Cross-references

- ARCHITECTURE.md §3 — full architectural profile
- EMERALD_ADAPTATION.md §pitch-agent — hardening playbook
- PROMPTS_CATALOG.md §A.1, §B.1 — verbatim prompt extractions
