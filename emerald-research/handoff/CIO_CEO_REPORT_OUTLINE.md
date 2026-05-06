# CIO_CEO_REPORT_OUTLINE.md

> **What this is.** Outline only. Section headings, suggested content, and
> pointers to source docs in the project knowledge base. **Not a draft.**
>
> **Audience assumption.** Joint CIO + CEO memo. CIO will care about
> platform, security, and recordkeeping cost; CEO about competitive
> positioning and capital allocation. The structure below covers both with
> overlapping evidence.

---

## Suggested length and format

- 4–6 pages prose + 1–2 page appendix (decision matrix + Q&A primer).
- Open with verdict in sentence 1; the rest is supporting evidence.
- Sidebar callouts for the regulatory items (Reg S-P 2024, RIA AML rule,
  Rule 204-2, V(A)) — these are likely the items the CIO and CEO will ask
  about first.

---

## §1 · Executive verdict (1 paragraph, sentence 1 = the answer)

Suggested anchor: *"Anthropic shipped a reference set of 10 finance-services
agents on [date]. None are deployable for Emerald as-is, all 10 are
deployable after a uniform set of platform-engineering investments, and
3–5 are directly relevant to our equity-research workflows. Recommendation:
[whatever decision Ed lands on]."*

Pointers: `EMERALD_ADAPTATION.md` §1, `ARCHITECTURE.md` §1.

## §2 · What did Anthropic ship (1 page, framed for non-technical reader)

Cover:
- 10 named agents (table — name + one-line workflow)
- Two deploy surfaces (Cowork + CMA); Emerald uses CMA only (firm policy)
- 66 underlying skills + 11 vendor MCP connectors (CapIQ, FactSet,
  Daloopa, Morningstar, etc.)
- Apache-2.0 licensed; Emerald can fork freely
- Architecture is markdown + YAML — readable by non-engineers

Pointers: `RECON.md` §3–§5, `SKILLS_INVENTORY.md` (whole), `README.md` of
the upstream repo (but flag that as untrusted-source under the operator's
threat model).

**Avoid:** internal jargon (orchestrator, subagent, MCP). Translate to
"agent-of-agents", "specialist worker", "data connector" for this audience.

## §3 · Applicability to Emerald (1 page — answers "should we care?")

Use the bucket table from `ARCHITECTURE.md` §1 as the spine. For each of
the 10 agents, state:
- Mandate fit (high / partial / low / out-of-mandate)
- Estimated analyst time saved per week (qualitative; refine with §4
  numbers if available)
- Reg S-P / Rule 204-2 / AML implications

Suggested condensed verdict table:

| Agent | Emerald fit | Why |
|---|---|---|
| earnings-reviewer | **Highest** | Covered-name post-earnings — core ER deliverable |
| market-researcher | **High** | Sector primers + ideas shortlists |
| model-builder | **High** | DCF + comps for ER |
| meeting-prep-agent | **Conditional** | Wealth-side workflow if Advisors arm runs advisor meetings |
| kyc-screener | **Required if RIA AML rule applies** | FinCEN/SEC rule effective 2026 |
| pitch-agent | **Out of mandate** | IB workflow, not RIA |
| gl-reconciler / month-end-closer | **Medium** | Corporate accounting, not portfolio |
| valuation-reviewer / statement-auditor | **Conditional** | Private-fund only |

Pointers: `ARCHITECTURE.md` §1 master table (full reasoning + 6-dimension
analysis per agent), `agents/<slug>/CLAUDE.md` per-agent mirrors.

## §4 · Cost to make these production-ready (1–1.5 pages — answers "what does this take?")

**This is the section the CIO will read most carefully.** Anchor on the
three repo-wide hooks the agents do not ship with:

### §4.1 · The three repo-wide hooks (shared cost)

1. **Rule 204-2 archive wrapper** — append-only log of every agent
   invocation with input/output/operator/model/MCPs/approval. ~platform-
   engineering month.
2. **§204A approval gate** — typed human-approval tool replacing the
   prose-only "stop and surface". ~2 weeks platform engineering + UI work.
3. **Vendor-egress proxy** — strip client identifiers before any CapIQ /
   FactSet / Daloopa query. ~platform-engineering month + CCO review.

### §4.2 · Per-agent deltas (incremental on top)

Reference `EMERALD_ADAPTATION.md` §2 — pick 1–3 agents you propose to
pilot and table only those agents' deltas. Don't enumerate all 10 — that
loses the executive reader.

### §4.3 · Eval suite (CFA V(A) Diligence)

The repo ships zero eval suite. Building one is mandatory before any
production use. Per agent:

- 5–10 historical-period golden inputs with known-correct outputs.
- Adversarial fixtures (prompt-injection corpus from PATTERNS.md §P2).
- Re-run on every model upgrade (Anthropic moves quickly — Opus 4.7 →
  4.8/4.9 etc.).

Pointers: `EMERALD_ADAPTATION.md` §1.1 / §1.2 / §1.5 / §1.6.

## §5 · What does *not* doing this cost (1 page — competitive framing)

This is the CEO frame.

- **Peer firms are adopting.** This is an industry-wide reference release
  (Anthropic announced [date]) — competitors with platform engineering will
  pilot in Q-this. Emerald's choice is "lead, fast-follow, or wait".
- **Cowork prohibition is firm policy** — but the agents are deployable via
  CMA (Managed Agents API). Cowork ban does not block adoption.
- **Anthropic is a primary AI vendor for Emerald** — engagement here
  influences future support and feature priority.
- **The patterns are reusable** — even if we don't pilot any of the 10
  templates, the architectural patterns (3-tier isolation, schema-validated
  readers, allowlisted handoffs, single-Write-holder) are how Emerald should
  author *all* future internal AI agents. Doing nothing means losing the
  reference template for safe agent design.

## §6 · How we might use these to build *better* agents for Emerald (1 page)

This is the section unique to Emerald — answers "what's in it for us
beyond using the templates as-is?"

Cover:
- Treat the repo as a primitives library — patterns are more valuable
  than individual agents.
- 5 candidate Emerald-authored agents (cite `EXTENSION_PLAYBOOK.md` §4):
  - `coverage-monitor` (daily coverage scan)
  - `compliance-letter-drafter`
  - `13F-tracker`
  - `client-suitability-monitor`
  - `corporate-action-impact`
- Each inherits the 10 patterns by construction.
- Skill-authoring path: Emerald can write firm-specific skills (position
  sizing, attribution framework, IPS letter format) using the
  `skill-creator` meta-skill. Skills are reusable across multiple agents.

Pointers: `PATTERNS.md` (whole), `EXTENSION_PLAYBOOK.md` §4 + §5.

## §7 · Workflow rebuild — analyst time savings (1 page — concrete examples)

CEO wants to see "what does this look like Tuesday morning". Cover:

- Earnings-week reshape: ~32h → ~12h analyst time per week (Q-end).
- Weekly sector primer: ~5h → ~1.5h.
- Day-in-the-life of an analyst on this stack — supervisor + judgment
  role, not doer.
- Phased rollout (Q1 foundation, Q2 first agent in prod, Q3 expansion).

Pointers: `WORKFLOW_DESIGN.md` §2 (earnings week), §3 (sector primer),
§6 (day-in-the-life), §8 (phased rollout).

## §8 · Risks and obligations (0.5–1 page)

Three risk buckets:

1. **Regulatory** — Reg S-P 2024 (acute on meeting-prep), Rule 204-2 +
   §204A across all agents, RIA AML rule on kyc-screener.
2. **Vendor egress** — CapIQ / FactSet / Daloopa receive query payloads
   reflecting research direction; firm-IP exposure if not redacted.
3. **CFA V(A) Diligence** — survivorship-bias in idea-generation; consensus
   snapshot drift; adversarial documents in any reader subagent.

For each: state the mitigation (egress proxy, eval suite, schema-validated
readers, etc.) and what triggers escalation.

Pointers: `EMERALD_ADAPTATION.md` §3, `ARCHITECTURE.md` §2.7 + §2.8.

## §9 · Decision asks (the close)

Frame each as a yes/no the CIO + CEO can act on:

- [ ] Approve Q1 platform foundation (3 hooks + first eval suite). Cost:
  [estimate].
- [ ] Approve Q2 pilot of 1 agent (proposed: `earnings-reviewer`) on N
  covered names.
- [ ] Approve Q3 expansion if Q2 KPIs hit — adding `market-researcher` +
  `model-builder` + first Emerald-authored agent.
- [ ] Approve Reg S-P 2024 Compliance scope for `meeting-prep-agent`
  pilot (decision needed: Advisors arm in scope or out).

State who needs to sign each line + by when.

---

## §10 · Appendix A: Decision matrix (for the back of the memo)

A one-page grid showing each of the 10 agents × 6 dimensions
(applicability, Reg S-P risk, Rule 204-2 burden, vendor egress, V(A) flag
density, hardening cost). Sourced from `ARCHITECTURE.md` §1 master table.

## §11 · Appendix B: Q&A primer (anticipated questions)

Pre-empt likely CIO/CEO questions with sourced one-paragraph answers:

- *"How is this different from our current AI tooling?"* — Different
  surface (file-based markdown agents, deployable as Managed Agents API);
  same vendor (Anthropic).
- *"Do we have to use Cowork?"* — No. CMA is the firm-permitted path. All
  patterns work in CMA mode (PATTERNS.md §P6).
- *"What's the risk if Anthropic deprecates this?"* — Apache-2.0 license;
  we own a fork. Patterns are vendor-agnostic.
- *"How long until our first pilot is in production?"* — Q2 if foundation
  ships in Q1.
- *"Will this replace analysts?"* — No. Reshape role from doer to
  supervisor + judgment. Time saved = capacity for more coverage / deeper
  research.
- *"What if Anthropic changes the underlying agents next month?"* — Our
  fork is at SHA `bb4a2b3...`; PROMPTS_CATALOG.md is a regression anchor;
  upstream changes are detectable and reviewable.

## §12 · Appendix C: Glossary (for non-technical readers)

| Term | Plain English |
|---|---|
| Agent | An AI workflow with a specific role + a recipe for using tools |
| Subagent | A specialist worker an agent dispatches |
| MCP (Model Context Protocol) | Standardized data connector — how the agent talks to FactSet/CapIQ/etc |
| Cowork | Anthropic's interactive product surface — firm-prohibited |
| CMA (Claude Managed Agents API) | Anthropic's headless deploy surface — firm-permitted |
| Skill | Domain-knowledge document the agent loads when relevant |
| Steering event | The user's request — short structured string |
| Handoff | One agent triggering another, with allowlist + validation |
| Schema-validated output | Agent output checked against a strict format before downstream use |

---

## Drafting tips for whoever writes the actual memo

- The verdict in sentence 1 is non-negotiable. Don't bury the lede.
- Cite specific source docs in footnotes (or links) so the CIO/CEO can
  drill into the evidence without rereading the memo.
- The §4 cost section is where executive credibility lives — be specific
  on engineering effort. Don't say "moderate"; say "~3 platform-engineer-
  months".
- The §5 "what does *not* doing this cost" frame is necessary for capital
  allocation — without it, the memo reads as request-for-budget rather
  than strategic-decision.
- The §9 decision asks must be signable. Decisions that aren't binary
  yes/no end up un-decided.
