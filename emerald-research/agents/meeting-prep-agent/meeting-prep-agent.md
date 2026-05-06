# meeting-prep-agent — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `meeting-prep-agent`
> shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Pre-meeting briefing pack from CRM + holdings + market context + suggested
agenda. Cite:
`plugins/agent-plugins/meeting-prep-agent/agents/meeting-prep-agent.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/meeting-prep-agent/agents/meeting-prep-agent.md` | 1-31 |
| CMA orchestrator manifest | `managed-agent-cookbooks/meeting-prep-agent/agent.yaml` | 1-30 |
| Profiler subagent (CRM + CapIQ) | `managed-agent-cookbooks/meeting-prep-agent/subagents/profiler.yaml` | 1-20 |
| News-reader subagent (UNTRUSTED inbound emails) | `managed-agent-cookbooks/meeting-prep-agent/subagents/news-reader.yaml` | 1-30 |
| News-reader output schema | `managed-agent-cookbooks/meeting-prep-agent/subagents/news-reader.yaml` | 17-30 |
| Pack-writer subagent (only Write) | `managed-agent-cookbooks/meeting-prep-agent/subagents/pack-writer.yaml` | 1-19 |
| Deploy notes | `managed-agent-cookbooks/meeting-prep-agent/README.md` | 1-31 |

## Dependencies

- **MCP egress:** **CRM (firm-internal NPI)**, CapIQ.
- **Skills:** `client-review`, `client-report`, `investment-proposal`,
  `pptx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas — REG S-P 2024 ACUTE

1. **CRM data is customer NPI by definition** — relationship history,
   holdings, recent activity all qualify. Reg S-P 2024 safeguarding rule
   applies to (a) the CRM MCP egress payloads, (b) the briefing-pack
   `.pptx` output, and (c) any logging Emerald adds.
2. **News-reader ingests inbound client emails** — an attacker with the
   client's email address can attempt to inject instructions via a
   crafted message. Schema-validated reader output is the defense
   (`news-reader.yaml:17-30`).
3. **CapIQ queries leak holdings context** — querying CapIQ with a
   client-derived ticker reveals to CapIQ which names the firm is
   researching for which client. Payload audit recommended.
4. **Talking points are suitability-adjacent** — "three to five items the
   advisor should raise" (`meeting-prep-agent.md:14`) is a specific
   recommendation surface. Mark-up gate by advisor before any client
   contact must be enforced, not just prose.
5. **No client-facing send invariant** at line 27 is prose-only.
6. **Partial Emerald relevance** — relevant to Emerald Advisors arm if
   advisor workflows are in scope; less relevant if the firm runs
   asset-management mandates only.

## Compliance bucket

**(b)** — Reg S-P 2024 hardening is the dominant line item; without it,
this agent is closer to (c). With Emerald's NPI controls + 204-2 +
advisor-mark-up gate, it is a workable (b).

## Cross-references

- ARCHITECTURE.md §6
- EMERALD_ADAPTATION.md §meeting-prep-agent
- PROMPTS_CATALOG.md §A.4, §B.4
