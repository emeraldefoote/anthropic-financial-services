# gl-reconciler — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `gl-reconciler`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

GL ↔ subledger reconciliation by trade date and asset class: find breaks,
trace root cause, route exception report for sign-off. Cite:
`plugins/agent-plugins/gl-reconciler/agents/gl-reconciler.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/gl-reconciler/agents/gl-reconciler.md` | 1-33 |
| CMA orchestrator manifest | `managed-agent-cookbooks/gl-reconciler/agent.yaml` | 1-50 |
| MCP server declarations | `managed-agent-cookbooks/gl-reconciler/agent.yaml` | 36-42 |
| **Reader subagent (canonical pattern)** | `managed-agent-cookbooks/gl-reconciler/subagents/reader.yaml` | 1-58 |
| Reader's "treat as data" prompt | `managed-agent-cookbooks/gl-reconciler/subagents/reader.yaml` | 11-15 |
| Reader output schema | `managed-agent-cookbooks/gl-reconciler/subagents/reader.yaml` | 35-58 |
| Critic subagent (re-verifies via trusted MCPs) | `managed-agent-cookbooks/gl-reconciler/subagents/critic.yaml` | 1-20 |
| Resolver subagent (only Write) | `managed-agent-cookbooks/gl-reconciler/subagents/resolver.yaml` | 1-18 |
| Security/handoff notes | `managed-agent-cookbooks/gl-reconciler/README.md` | 1-36 |

## Dependencies

- **MCP egress:** **internal-gl, subledger** — both firm-internal, no
  third-party data leaves the perimeter. This is the cleanest egress
  posture in the repo.
- **Skills:** `gl-recon`, `break-trace`, `audit-xls`, `xlsx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas

1. **Counterparty/custodian statements are externally authored** — highest
   prompt-injection surface in the repo. The canonical reader-isolation
   pattern is implemented here and serves as the reference for the other
   8 readers.
2. **Three-stage trust validation:** untrusted reader → critic re-verifies
   each break against trusted internal MCPs → resolver writes report.
   Critic re-verification is the V(A) reasonable-basis safeguard against
   reader hallucination or injection.
3. **"No ledger posting" invariant** at `gl-reconciler.md:29` is prose-only.
   Emerald should add a unit-test that fails the deploy if the resolver
   yaml ever gains a posting-capable MCP.
4. **internal-gl + subledger MCPs must map to Emerald's actual systems**
   before deploy — the CMA env vars (`GL_MCP_URL`, `SUBLEDGER_MCP_URL`)
   are placeholders.
5. **Medium Emerald relevance** — corporate-accounting workflow, not
   portfolio. Useful for Emerald Advisors entity-level GL only if Emerald
   runs a fund-admin layer in-house.

## Compliance bucket

**(b)** — design is exemplary; hardening is the repo-wide three (Cowork
prohibition, 204-2, §204A audit trail) plus the never-post invariant test.

## Cross-references

- ARCHITECTURE.md §8
- EMERALD_ADAPTATION.md §gl-reconciler
- PROMPTS_CATALOG.md §A.6, §B.6, §D (canonical schema)
