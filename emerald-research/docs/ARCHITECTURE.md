# ARCHITECTURE.md — Phase 2 Architectural Analysis

> **Status.** Per-agent architectural profiles, subagent trust-tier mappings, and
> compliance-bucket assignments for the 10 named agents in SOURCE_REPO at SHA
> `bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d`. Verbatim system-prompt extraction
> (`untrusted-source` fences) is the Phase 3 PROMPTS_CATALOG.md artifact; here
> we cite by `path:line-range` and synthesize.

---

## 1 · Master compliance bucket summary

Per Operating Constraint #5, every agent is assigned exactly one of:

- **(a)** works out of the box for a regulated adviser
- **(b)** requires Emerald hardening before production use
- **(c)** incompatible with regulated-entity posture as written

> **All ten agents are bucket (b).** This is not fence-sitting; it is a
> uniform conclusion driven by three repo-wide gaps that each agent inherits
> equally: (i) zero built-in Rule 204-2 recordkeeping hooks, (ii) no audit
> trail of human approvals required by §204A / §15(g) "reasonably designed"
> supervision, and (iii) Cowork-mode deployment is firm-prohibited but is the
> *primary* surface the repo ships against. Each row below specifies the
> *additional* per-agent hardening on top of those three. No agent is bucket
> (c) because the design is sound — the hardening is at the deployment +
> instrumentation layer, not the agent prompt or workflow itself. No agent is
> (a) because at least the three repo-wide gaps must be closed before
> production use.

| # | Agent | Bucket | Relevance to Emerald | Top-priority hardening (delta beyond repo-wide) |
|---|---|:---:|---|---|
| 1 | `pitch-agent` | (b) | **Out of mandate** — IB pitch creation, not RIA work | Skip deployment; document only |
| 2 | `market-researcher` | (b) | **High** — sector primers, ideas shortlists | Survivorship-bias review of CapIQ/FactSet idea-generation universe (CFA V(A)); vendor-egress payload audit |
| 3 | `earnings-reviewer` | (b) | **Highest** — covered-name post-earnings | Provenance chain on coverage-model deltas; vendor-egress audit; transcript-reader injection-defense regression test |
| 4 | `meeting-prep-agent` | (b) | Partial — Emerald Advisors arm | **Reg S-P 2024 acute** — NPI inventory + customer-info egress controls on CRM MCP; news-reader inbound-email injection defense |
| 5 | `model-builder` | (b) | High — DCF / comps for ER | Bash-sandbox attestation for `builder` subagent; model-provenance archive (V(A)) |
| 6 | `gl-reconciler` | (b) | Medium — corporate accounting only, not portfolio | Map `internal-gl` and `subledger` MCPs to Emerald's actual systems before deploy |
| 7 | `kyc-screener` | (b) | High if RIA AML rule (effective 2026) applies | AML record retention scheme; sanctions-list provider attestation; rules-engine alignment with firm KYC policy |
| 8 | `valuation-reviewer` | (b) | Conditional — only if Emerald operates a private fund | Marks-to-policy variance threshold; LP-egress controls on publisher output |
| 9 | `month-end-closer` | (b) | Medium — corp-accounting, not portfolio | JE-staging-only enforcement; never-post invariant test |
| 10 | `statement-auditor` | (b) | Conditional — same as valuation-reviewer | Tie-out-source provenance; pass/hold human override gate |

---

## 2 · Cross-cutting architectural findings

These observations apply to all 10 agents and underlie the per-agent profiles
in §3–§12.

### 2.1 · Model selection (§204A diligence input)

All 10 orchestrators and all 30 subagents specify **`model: claude-opus-4-7`**.
Cite: every `managed-agent-cookbooks/<slug>/agent.yaml:4` and every subagent
`.yaml:2`. No agent uses Sonnet or Haiku. No fallback model, no other provider.

### 2.2 · Cowork frontmatter vs CMA orchestrator: the Write-tool divergence (resolves OQ-6)

The `agents/<slug>.md` YAML frontmatter (Cowork-side declaration) includes
`Write` and `Edit` for 5 of 10 agents:

| Agent | Cowork `tools:` (frontmatter) | CMA orchestrator `agent_toolset` (yaml) |
|---|---|---|
| pitch-agent | `Read, Write, Edit, mcp__capiq__*` (`pitch-agent.md:4`) | `read, grep, glob` only (`managed-agent-cookbooks/pitch-agent/agent.yaml:14-16`) |
| market-researcher | `Read, Write, Edit, mcp__capiq__*, mcp__factset__*` (`market-researcher.md:4`) | `read, grep, glob` only (`managed-agent-cookbooks/market-researcher/agent.yaml:14-16`) |
| earnings-reviewer | `Read, Write, Edit, mcp__factset__*, mcp__daloopa__*` (`earnings-reviewer.md:4`) | `read, grep, glob` only (`managed-agent-cookbooks/earnings-reviewer/agent.yaml:14-16`) |
| meeting-prep-agent | `Read, Write, mcp__crm__*, mcp__capiq__*` (`meeting-prep-agent.md:4`) | `read, grep, glob` only (`managed-agent-cookbooks/meeting-prep-agent/agent.yaml:14-16`) |
| model-builder | `Read, Write, Edit, mcp__capiq__*, mcp__daloopa__*` (`model-builder.md:4`) | `read, grep, glob` only (`managed-agent-cookbooks/model-builder/agent.yaml:14-16`) |
| gl-reconciler | `Read, Grep, Glob, mcp__internal-gl__*, mcp__subledger__*` (`gl-reconciler.md:4`) | matches |
| kyc-screener | `Read, Grep, Glob, mcp__screening__*` (`kyc-screener.md:4`) | matches |
| valuation-reviewer | `Read, Grep, Glob, mcp__portfolio__*` (`valuation-reviewer.md:4`) | matches |
| month-end-closer | `Read, Grep, Glob, mcp__internal-gl__*` (`month-end-closer.md:4`) | matches |
| statement-auditor | `Read, Grep, Glob, mcp__nav__*` (`statement-auditor.md:4`) | matches |

**Resolution.** The Cowork frontmatter is *Cowork-specific* — Cowork installs
the agent and grants the listed tools to the orchestrator session. The CMA
`agent.yaml` *deliberately strips Write/Edit/Bash from the orchestrator* and
isolates them in the writer-tier subagent. **In CMA mode, the orchestrator is
read-only across all 10 agents.** The 5 "matches" rows above (gl-reconciler,
kyc-screener, valuation-reviewer, month-end-closer, statement-auditor) already
have Cowork frontmatter that is read-only — these 5 are the fund-admin /
ops-tier agents, treated as the highest-untrusted-input agents.

**Compliance implication.** For Emerald (Cowork prohibited), CMA is the only
deployment path. The Cowork-side frontmatter `Write` declarations are **not
loaded** by CMA, so the CMA-mode trust tiers as described in each cookbook
README hold. The Cowork-mode looser permissions become a moot point.

### 2.3 · The canonical three-tier isolation pattern

Eight of ten agents adopt the same trust-tier shape (one variant: `pitch-agent`
and `model-builder` skip the untrusted-reader tier because their inputs come
from MCP-vended trusted vendor data only):

```
Steering event ──▶ Orchestrator ─┬──▶ Reader subagent  (UNTRUSTED ingestion)
                                 │     • Read + Grep only
                                 │     • No MCP, no Write, no callable_agents
                                 │     • Schema-validated JSON output via output_schema
                                 │
                                 ├──▶ Critic / runner / engine  (TRUSTED MCP query, re-verify)
                                 │     • Read + Grep + read-only firm/vendor MCP
                                 │     • No Write
                                 │
                                 └──▶ Writer subagent  (file artifact assembly)
                                       • Read + Write + Edit
                                       • No MCP, no untrusted ingestion
                                       • Output: ./out/<artifact>
```

Reader subagents that ingest untrusted documents carry a **literal in-prompt
instruction** to treat document content as data, not directives. Verbatim
extraction is Phase 3, but cite locations:

- `managed-agent-cookbooks/gl-reconciler/subagents/reader.yaml:11-15` (canonical phrasing)
- `managed-agent-cookbooks/market-researcher/subagents/sector-reader.yaml:4-7`
- `managed-agent-cookbooks/earnings-reviewer/subagents/transcript-reader.yaml:4-7`
- `managed-agent-cookbooks/meeting-prep-agent/subagents/news-reader.yaml:4-7`
- `managed-agent-cookbooks/kyc-screener/subagents/doc-reader.yaml:4-7`
- `managed-agent-cookbooks/valuation-reviewer/subagents/package-reader.yaml:4-7`
- `managed-agent-cookbooks/month-end-closer/subagents/ledger-reader.yaml:4-7`
- `managed-agent-cookbooks/statement-auditor/subagents/statement-reader.yaml:4-7`

### 2.4 · Schema validation as the inbound-injection defense

Every reader subagent declares an `output_schema:` block (consumed by the
deploy harness via `scripts/validate.py`, *not* an API field per
`managed-agent-cookbooks/gl-reconciler/subagents/reader.yaml:31-34`). Two defensive properties of every
schema:

1. **Length caps.** `maxLength: <n>` on every string, `maxItems: <n>` on every
   array.
2. **Character-class restriction.** `pattern: "^[A-Za-z0-9 .,%$()_/:-]+$"` (or
   similar narrow whitelist) on string fields.

Together these mean an attacker-controlled instruction in a counterparty
statement — even one that the reader's prompt fails to neutralize — cannot
reach the orchestrator intact: shell metachars, markdown code fences, angle
brackets, curly braces, newlines, and backticks are all rejected.

Per-reader schema citations:

| Reader | Schema location | Notable patterns |
|---|---|---|
| `gl-reconciler-reader` | `reader.yaml:35-58` | account `^[A-Za-z0-9._:-]+$`, evidence_refs `^[A-Za-z0-9 ._/:#-]+$` |
| `market-sector-reader` | `sector-reader.yaml:17-32` | claim `^[A-Za-z0-9 .,%$()_/&:-]+$`, source `^[A-Za-z0-9 .,_/:-]+$` |
| `earnings-transcript-reader` | `transcript-reader.yaml:17-30` | ticker `^[A-Z.]+$`, guidance_notes `^[A-Za-z0-9 .,%$()_/:-]+$` |
| `briefing-news-reader` | `news-reader.yaml:17-30` | headline `^[A-Za-z0-9 .,%$()_/:-]+$` |
| `kyc-doc-reader` | `doc-reader.yaml:17-37` | legal_name `^[A-Za-z0-9 .,&_/-]+$`, country `^[A-Z]{2}$` |
| `valuation-package-reader` | `package-reader.yaml:17-33` | portco_id `^[A-Za-z0-9_-]+$`, method enum |
| `close-ledger-reader` | `ledger-reader.yaml:17-33` | ref `^[A-Za-z0-9 ._/:-]+$`, period `^[0-9]{4}-[0-9]{2}$` |
| `stmt-statement-reader` | `statement-reader.yaml:17-33` | lp_id `^[A-Za-z0-9_-]+$` |
| `pitch-researcher` (no untrusted-doc tier — pulls from MCPs only, but still schema-validated) | `researcher.yaml:21-47` | ticker `^[A-Z.]+$` |
| `model-data-puller` (same: trusted-MCP only) | `data-puller.yaml:20-30` | ticker `^[A-Z.]+$` |

### 2.5 · Cross-agent handoffs (allowlisted, no direct calls)

Agents never invoke each other via `callable_agents` (CMA preview limit:
depth-1; cite `managed-agent-cookbooks/README.md:34`). Cross-agent flow:

1. Orchestrator emits a `handoff_request` blob in its output text.
2. `scripts/orchestrate.py` (reference loop) re-extracts the blob, validates
   `target_agent` against an **eight-name allowlist** at line 22-26, and
   schema-validates the `payload` (event maxLength 2000, context_ref pattern
   `^[A-Za-z0-9 ._/:#-]+$`) at lines 27-37.
3. Validated handoff becomes a new steering event to the target agent.

Cite: `scripts/orchestrate.py:6-37`. Defensive note: handoff blobs surface
*downstream of untrusted-document readers*, so a malicious document could
attempt to coerce an echo of a fake handoff. The allowlist + schema validation
are the rails that block it. Phase 3 will recommend Emerald replace the
text-echo channel with a typed tool call (the script's own header comment
flags this as the preferred production design — `orchestrate.py:11-12`).

Documented handoff edges (from cookbook READMEs):

| From | → To | Trigger |
|---|---|---|
| `pitch-agent` | `model-builder` | Thesis change after MD feedback (`managed-agent-cookbooks/pitch-agent/README.md:31`) |
| `market-researcher` | `model-builder` | Single name from ideas shortlist (`managed-agent-cookbooks/market-researcher/README.md:31`) |
| `earnings-reviewer` | `model-builder` | Earnings-driven thesis change (`managed-agent-cookbooks/earnings-reviewer/README.md:31`) |
| `gl-reconciler` | `month-end-closer` | Verified breaks fold into close (`managed-agent-cookbooks/gl-reconciler/README.md:36`) |
| `valuation-reviewer` | `gl-reconciler` | Flagged portcos (`managed-agent-cookbooks/valuation-reviewer/README.md:31`) |

`scripts/orchestrate.py:22-26` allowlist actually contains 10 entries (all 10
named agents) — broader than the 5 documented edges, leaving headroom for
operator-defined flows.

### 2.6 · Persistence and logging — the load-bearing gap

**No agent in the repo has any built-in audit, recordkeeping, or
human-approval-capture instrumentation.** This is the foundational §204A /
§15(g) "reasonably designed" + Rule 204-2 gap. Specifically:

- File outputs land in `./out/<artifact>` with deterministic names (e.g.
  `./out/pitch-<target>.pptx`, `./out/model-<ticker>.xlsx`). No log of who
  approved them, when, or against what input. Cite: every cookbook README
  artifact path callout.
- The `append:` clause in every `agent.yaml` (`...agent.yaml:8`) sets headless
  mode but contains no logging requirement.
- `scripts/orchestrate.py` is explicitly REFERENCE ONLY (`orchestrate.py:3-6`)
  and does not persist steering events, handoffs, or outputs.
- `scripts/validate.py` validates worker output but does not archive it.
- No agent declares a `Bash` tool to a logging endpoint; no agent uses `Write`
  to write a transaction log.
- No agent emits OpenTelemetry, Datadog, Splunk, or any other observability
  signal.
- The "Stop and surface for review" guardrails (in 6 of 10 system prompts) are
  **prose-only** instructions with no enforcement mechanism. Cite:
  `pitch-agent.md:32`, `market-researcher.md:32`, `earnings-reviewer.md:24`,
  `model-builder.md:24,30`, `meeting-prep-agent.md:22`, etc.

For Emerald: every agent must be wrapped in a deploy-time hook (likely a
`scripts/orchestrate.py` derivative) that captures (input, output, timestamp,
operator, model, model-version, prompt-hash, mcp-server-set) tuples and
archives them in a Rule 204-2-compliant store with the standard 5-year +
2-year-onsite retention. This is the largest single Emerald-adaptation line
item and applies uniformly to all 10 agents. Phase 3 EMERALD_ADAPTATION.md
will specify the schema.

### 2.7 · Vendor data egress map

Every MCP request sends prompt context to the vendor's MCP endpoint. For
Reg S-P 2024 customer-information handling and for general firm-IP protection,
this is a non-trivial egress surface. Per-agent MCP egress at the orchestrator
+ subagent level:

| Agent | Egress destinations (read-only, but content of query is sent) |
|---|---|
| pitch-agent | CapIQ, Daloopa |
| market-researcher | CapIQ, FactSet |
| earnings-reviewer | FactSet, Daloopa |
| meeting-prep-agent | **CRM (firm-internal NPI)**, CapIQ |
| model-builder | CapIQ, Daloopa |
| gl-reconciler | **internal-gl, subledger** (firm systems) |
| kyc-screener | screening (third-party sanctions provider — KYC docs not sent, but party names are) |
| valuation-reviewer | **portfolio** (firm system) |
| month-end-closer | **internal-gl** (firm system) |
| statement-auditor | **nav** (firm system) |

**Bold** entries are firm-internal MCPs that Emerald would map to its own
backend; querying them does not egress NPI to third parties. CapIQ / Daloopa /
FactSet queries DO leave the Emerald perimeter and must be reviewed under the
firm's vendor-data sharing policy.

For `kyc-screener`, the screening MCP receives party names + identifiers — by
design, since that is the screening service's input. This is intended,
documented egress, but the data classification is sensitive (potential PEP
status, screening hits) and warrants a vendor-attestation review in Phase 3.

### 2.8 · CFA V(A) diligence flags (Phase-2 surface; remediation in Phase 3)

| Concern | Affected agents | Evidence |
|---|---|---|
| **Survivorship bias in idea generation** — CapIQ/FactSet equity universes default to current-listed names. `idea-generation` skill output may exclude delisted underperformers, biasing thematic shortlists upward. | `market-researcher` (uses `idea-generation`), `pitch-agent` (uses `comps-analysis` for peer universe) | `market-researcher.md:25`; `idea-generation` skill location: `plugins/vertical-plugins/equity-research/skills/idea-generation/SKILL.md` (deep-dive deferred to Phase 3) |
| **Look-ahead bias if used for backtesting** — every agent that pulls "consensus" from FactSet pulls *current-as-of* consensus. If an Emerald analyst uses these agents to assemble a historical backtest panel, consensus-as-of mismatches with trade-date will leak future information. The agents are not designed for backtest assembly, but no in-prompt guardrail prevents misuse. | `earnings-reviewer`, `market-researcher`, `model-builder`, `pitch-agent` | None of the system prompts include a "do not use for backtest assembly" guardrail. |
| **Model-assumption provenance** — `model-builder` lets the user supply assumptions (e.g. `wacc: 0.085`). The model-builder system prompt says "Hardcoded assumptions are labeled with source or marked `[ASSUMPTION]`" (`model-builder.md:29`) but the labeling lives inside the Excel file, not in any retained log. Reproducibility under V(A) requires an external assumption-set archive. | `model-builder`, `pitch-agent` (via lbo-model + dcf-model skills) | `model-builder.md:28-30` |
| **Consensus snapshot drift** — `earnings-reviewer` pulls consensus during a coverage update; if the analyst re-runs the same period later, FactSet may have repointed historical consensus due to provider corrections. This is a reproducibility gap, not an active bias, but Rule 204-2 archival must capture the consensus snapshot at note-write time. | `earnings-reviewer` | `earnings-reviewer.md:19-23` |
| **Demo data realism in steering examples** — Real public tickers (NVDA, MSFT, TGT, SHOP, CRWD, PANW, SNOW) appear in `steering-examples.json` files (cite per RECON §6). An Emerald analyst running these literally will produce output that *looks like* a real coverage product but with un-vetted vendor settings. | All agents shipping steering examples | every `managed-agent-cookbooks/<slug>/steering-examples.json` |

### 2.9 · Repository defensive posture (positive findings for §204A "reasonably designed")

The repo's design itself contributes positively to the "reasonably designed"
standard, even before Emerald's hardening overlay:

| Defense | Evidence |
|---|---|
| Reader subagents have no Write, no MCP, no callable_agents | every reader yaml, e.g. `reader.yaml:17-29` |
| Reader output is jsonschema-validated with length + char-class caps | every `output_schema:` block (cite §2.4) |
| Cross-agent handoffs are allowlisted + payload-validated | `scripts/orchestrate.py:22-37` |
| All MCPs are explicitly `read-only` in default config | inline comments in `managed-agent-cookbooks/gl-reconciler/agent.yaml:30,34`, plus pattern repeated |
| Writer subagent never opens untrusted content directly | every writer yaml header comment, e.g. `deck-writer.yaml:5-7`, `note-writer.yaml:5-7`, `resolver.yaml:5-7` |
| Steering events are short structured strings, not free-form documents | every `steering-examples.json` |
| Repo CI runs gitleaks v8.28.0 + Anthropic-internal-string scrub on every PR/push | `.github/workflows/secret-scan.yml:13-31` |
| Cowork prohibition is *not* a fatal incompatibility because every agent has a CMA cookbook | every `managed-agent-cookbooks/<slug>/agent.yaml` |

---

## 3 · `pitch-agent`

### 3.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "End-to-end investment banking pitch agent ... pulls comps and precedents from market data, builds a DCF and football-field valuation in Excel, and generates a branded pitch deck on the bank's PowerPoint template." | `pitch-agent.md:3` |
| Cowork plugin | `plugins/agent-plugins/pitch-agent/` | dir |
| CMA cookbook | `managed-agent-cookbooks/pitch-agent/` | dir |
| System prompt | `plugins/agent-plugins/pitch-agent/agents/pitch-agent.md:1-36` | full file |
| Model | claude-opus-4-7 (orchestrator + all 3 subagents) | `agent.yaml:4`, each subagent `:2` |
| Inputs | Target ticker/name + one-line situation | `pitch-agent.md:11,18`, `steering-examples.json` |
| Outputs | `./out/pitch-<target>.pptx`, `./out/model.xlsx` | `managed-agent-cookbooks/pitch-agent/README.md:29` |
| MCP egress | CapIQ, Daloopa (via `mcp__capiq__*` in frontmatter; `agent.yaml:17-22` for CMA) | |

### 3.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | Has output_schema? | Cite |
|---|:---:|---|---|:---:|---|
| `pitch-researcher` | No (MCP-only) | read, grep | capiq, daloopa | yes (`researcher.yaml:21-47`) | `researcher.yaml:1-47` |
| `pitch-modeler` | No | read, **bash** | capiq, daloopa | no | `modeler.yaml:1-23` |
| `pitch-deck-writer` (Write-holder) | No | read, write, edit | none | no | `deck-writer.yaml:1-20` |

**Notable:** `modeler` runs Python via Bash for valuations (`modeler.yaml:14`).
Bash sandbox attestation required for Emerald (Phase 3).

### 3.3 Data flow

1. Orchestrator scopes ask, identifies 5–8 trading comps + 5–10 precedents (`pitch-agent.md:18`).
2. Orchestrator calls `sector-overview` skill for situation overview (`pitch-agent.md:19`).
3. Orchestrator dispatches `pitch-researcher` → CapIQ for trading multiples + precedent data + filings (`pitch-agent.md:20`, `researcher.yaml:14-15`).
4. Orchestrator calls `comps-analysis` skill (`pitch-agent.md:21`).
5. Orchestrator dispatches `pitch-modeler` → builds DCF/LBO via Python+CapIQ/Daloopa, returns JSON (`pitch-agent.md:22-23`, `modeler.yaml:4-8`).
6. Orchestrator calls `dcf-model`, `3-statement-model`, `audit-xls` skills (`pitch-agent.md:23,26`).
7. Football-field assembled (`pitch-agent.md:24`).
8. Orchestrator dispatches `pitch-deck-writer` to populate bank PPT template + run `ib-check-deck` (`pitch-agent.md:25-26`, `deck-writer.yaml:5-7`).
9. **Two human-review gates** — after Excel build, after deck generation (`pitch-agent.md:32`).

### 3.4 Persistence / logging

Per §2.6: none. Outputs land in `./out/`; no audit trail captures the
"banker approves each artifact" gate from `pitch-agent.md:32`.

### 3.5 Compliance bucket: **(b)**

| Dimension | Verdict | Reasoning |
|---|---|---|
| Reg S-P 2024 customer info | **N/A** — no customer information in workflow; pitch targets are public companies. | |
| Rule 204-2 recordkeeping | **Gap** — repo-wide; no archival of input scoping, vendor query payloads, draft artifacts, or human-approval moments. | |
| §204A / §15(g) "reasonably designed" | **Gap** — repo-wide; "stop and surface for review" is prose-only. | `pitch-agent.md:32` |
| Cowork prohibition | **Hardening** — deploy via CMA only; CMA orchestrator already enforces read-only. | §2.2 |
| Vendor data egress | Acceptable — CapIQ + Daloopa both common buy-side vendors; queries reveal target name + sector. | `agent.yaml:17-22` |
| Prompt injection surface | **Low** — no untrusted-doc reader; all inputs are MCP-vended structured data. | `managed-agent-cookbooks/pitch-agent/README.md:21` |

**Net: (b)**, but with the qualification that this agent is **out of Emerald's
mandate** (RIA does not produce IB pitches). Phase 3 will recommend
documenting only, not deploying.

### 3.6 CFA V(A) flags

- **Survivorship bias** in `comps-analysis` peer universe (CapIQ default).
- **Football-field methodology mix** (DCF, LBO, comps, precedents) is standard
  but the repo does not surface assumption-set provenance. (Inherited from
  `dcf-model` / `lbo-model` skills — Phase 3 deep-dive.)

---

## 4 · `market-researcher`

### 4.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Sector or thematic market research — industry overview, competitive landscape, trading-comps spread of the peer set, and a thematic ideas shortlist — packaged as a research note with optional slides." | `market-researcher.md:3` |
| System prompt | `plugins/agent-plugins/market-researcher/agents/market-researcher.md:1-37` | full file |
| Inputs | Sector or theme + one-line angle | `market-researcher.md:11,21` |
| Outputs | `./out/primer-<sector>.docx` (+ optional `.pptx`) | `managed-agent-cookbooks/market-researcher/README.md:29` |
| MCP egress | CapIQ, FactSet | `agent.yaml:17-22` |

### 4.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `market-sector-reader` | **Yes** (third-party reports + issuer materials) | read, grep | none | yes (`sector-reader.yaml:17-32`) | `sector-reader.yaml:1-32` |
| `market-comps-spreader` | No | read, grep | capiq, factset | no | `comps-spreader.yaml:1-20` |
| `market-note-writer` (Write-holder) | No | read, write, edit | none | no | `note-writer.yaml:1-19` |

### 4.3 Data flow

1. Orchestrator scopes sector/theme/angle, defines 8–15-name universe (`market-researcher.md:21`).
2. Orchestrator calls `sector-overview` skill (`market-researcher.md:22`).
3. Orchestrator dispatches `market-sector-reader` → ingests untrusted third-party reports, returns schema-validated facts JSON (`market-researcher.md:30`, `sector-reader.yaml:4-7`).
4. Orchestrator calls `competitive-analysis` skill (`market-researcher.md:23`).
5. Orchestrator dispatches `market-comps-spreader` → CapIQ/FactSet trading multiples (`market-researcher.md:24`, `comps-spreader.yaml:4-6`).
6. Orchestrator calls `idea-generation` skill (`market-researcher.md:25`).
7. Orchestrator dispatches `market-note-writer` → assembles `.docx` (+ optional `.pptx`) (`market-researcher.md:26`, `note-writer.yaml:5-9`).
8. **Two human-review gates** — after comps spread, after note draft (`market-researcher.md:32`).
9. Explicit "no distribution" guardrail (`market-researcher.md:33`).

### 4.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | N/A — no customer information |
| Rule 204-2 | Gap (repo-wide); ideas-shortlist publication is research product → must be retained |
| §204A / §15(g) | Gap (repo-wide); "no distribution" is prose-only |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | Acceptable; CapIQ + FactSet queries reveal sector/theme + universe |
| Prompt injection | **Material** — `sector-reader` is the highest-injection-risk subagent (third-party PDFs); defense via §2.3 + §2.4 schema |

### 4.5 CFA V(A) flags (Emerald-relevant)

- **Survivorship bias acute** — `idea-generation` against current CapIQ universe; ideas shortlist is research product. **Phase 3 must mandate** delisted-name backfill review or explicit disclaimer.
- **Selection bias** — "8–15 names that define the space" (`market-researcher.md:21`) is operator-defined; reasonable basis V(A) requires documenting the universe-construction rule.

---

## 5 · `earnings-reviewer`

### 5.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Processes an earnings event end to end — reads the call transcript and filings, updates the coverage model, and drafts the post-earnings note." | `earnings-reviewer.md:3` |
| System prompt | `plugins/agent-plugins/earnings-reviewer/agents/earnings-reviewer.md:1-34` | full file |
| Inputs | Ticker + reporting period | `earnings-reviewer.md:11,19` |
| Outputs | `./out/model-<ticker>.xlsx`, `./out/note-<ticker>.docx` | `managed-agent-cookbooks/earnings-reviewer/README.md:29` |
| MCP egress | FactSet, Daloopa | `agent.yaml:17-22` |

### 5.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `earnings-transcript-reader` | **Yes** (call transcripts + press releases) | read, grep | none | yes (`transcript-reader.yaml:17-30`) | `transcript-reader.yaml:1-30` |
| `earnings-model-updater` | No | read, grep | factset, daloopa | no | `model-updater.yaml:1-21` |
| `earnings-note-writer` (Write-holder) | No | read, write, edit | none | no | `note-writer.yaml:1-19` |

### 5.3 Data flow

1. Orchestrator pulls actuals/consensus/10-Q/8-K from FactSet+Daloopa (`earnings-reviewer.md:19`).
2. Orchestrator dispatches `earnings-transcript-reader` → ingests untrusted transcript+press release, returns ticker/period/actuals JSON (`transcript-reader.yaml:4-7`).
3. Orchestrator calls `earnings-analysis` skill — guidance, tone, dodged Q&A (`earnings-reviewer.md:20`).
4. Orchestrator dispatches `earnings-model-updater` → drops actuals into coverage model, rolls estimates (`earnings-reviewer.md:21`).
5. Orchestrator calls `audit-xls` (`earnings-reviewer.md:22`).
6. Orchestrator dispatches `earnings-note-writer` → drafts note via `morning-note` skill (`earnings-reviewer.md:23`).
7. Stage as drafts, do not publish (`earnings-reviewer.md:24,30`).

### 5.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | N/A — no customer information |
| Rule 204-2 | **High-priority gap** — coverage notes are published research; consensus snapshot at note-time must be archived |
| §204A / §15(g) | Gap (repo-wide); "never publish" is prose-only |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | Acceptable; ticker + period are minimal |
| Prompt injection | **Material** — transcript-reader; defense per §2.3, §2.4 |

### 5.5 CFA V(A) flags (Emerald-relevant)

- **Consensus reproducibility** — FactSet consensus is mutable; archival of the
  consensus snapshot at draft time is required for V(A) reasonable-basis review.
- **Variance commentary fidelity** — variance vs. consensus and prior estimate
  flagged (`earnings-reviewer.md:13`); Phase 3 should require source-cell
  citations in the model deltas.

---

## 6 · `meeting-prep-agent`

### 6.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Builds a briefing pack before a client or prospect meeting — relationship history from CRM, holdings and recent activity, market context, and a suggested agenda." | `meeting-prep-agent.md:3` |
| System prompt | `plugins/agent-plugins/meeting-prep-agent/agents/meeting-prep-agent.md:1-31` | full file |
| Inputs | Client ID + calendar-event ID | `meeting-prep-agent.md:11,18-19` |
| Outputs | `./out/briefing-<client>.pptx` | `managed-agent-cookbooks/meeting-prep-agent/README.md:29` |
| MCP egress | **CRM (firm-internal NPI)**, CapIQ | `agent.yaml:17-22` |

### 6.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `briefing-profiler` | No (CRM is firm-trusted) | read, grep | crm, capiq | no | `profiler.yaml:1-20` |
| `briefing-news-reader` | **Yes** (inbound emails + news articles) | read, grep | none | yes (`news-reader.yaml:17-30`) | `news-reader.yaml:1-30` |
| `briefing-pack-writer` (Write-holder) | No | read, write, edit | none | no | `pack-writer.yaml:1-19` |

### 6.3 Data flow

1. Orchestrator dispatches `briefing-profiler` → CRM + CapIQ for relationship + holdings + open items (`meeting-prep-agent.md:18-19`, `profiler.yaml:4-7`).
2. Orchestrator dispatches `briefing-news-reader` → summarizes inbound emails + news (untrusted) (`meeting-prep-agent.md:20`, `news-reader.yaml:4-7`).
3. Orchestrator calls `client-review` + `client-report` skills (`meeting-prep-agent.md:21`).
4. Orchestrator dispatches `briefing-pack-writer` → assembles `.pptx` (`pack-writer.yaml:5-7`).
5. **Advisor reviews before meeting** — pack is for advisor, not client (`meeting-prep-agent.md:22,27`).

### 6.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| **Reg S-P 2024 customer info** | **Acute hardening required** — relationship history + holdings + recent activity are NPI; CRM MCP egress must be policy-controlled; pack output retention must follow Reg S-P safeguarding rule. |
| Rule 204-2 | High-priority gap — meeting prep packs are advisory work product; retention applies. |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | **CapIQ queries with client-derived ticker context** could leak which holdings the firm is researching for which client; payload audit required. |
| Prompt injection | **Material** — news-reader ingests inbound client emails (which an attacker can send into the firm); defense per §2.3, §2.4. |

### 6.5 CFA V(A) flags (Emerald-relevant)

- **Suggested agenda quality** — agenda is a recommendation generated from
  relationship + market data; needs an explicit "advisor edits before client
  contact" gate (already present in prose at `meeting-prep-agent.md:22,27`,
  but no enforcement).
- **Talking-point bias** — "three to five items the advisor should raise"
  (`meeting-prep-agent.md:14`) is suitability-adjacent. If used uncritically
  could imply specific recommendations; Phase 3 must require advisor mark-up
  before any use.

---

## 7 · `model-builder`

### 7.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Builds DCF, LBO, three-statement, and trading-comps models live in Excel from a ticker and assumption set." | `model-builder.md:3` |
| System prompt | `plugins/agent-plugins/model-builder/agents/model-builder.md:1-34` | full file |
| Inputs | Ticker + model type + assumption set | `model-builder.md:11,20` |
| Outputs | `./out/model.xlsx` | `managed-agent-cookbooks/model-builder/README.md:29` |
| MCP egress | CapIQ, Daloopa | `agent.yaml:17-22` |

### 7.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `model-data-puller` | No | read, grep | capiq, daloopa | yes (`data-puller.yaml:20-30`) | `data-puller.yaml:1-30` |
| `model-builder-builder` (Write-holder) | No | read, write, edit, **bash** | none | no | `builder.yaml:1-23` |
| `model-auditor` | No | read, grep | none | no | `auditor.yaml:1-17` |

### 7.3 Data flow

1. Orchestrator dispatches `model-data-puller` → CapIQ/Daloopa historicals + consensus (`model-builder.md:20`, `data-puller.yaml:4-6`).
2. Orchestrator calls `dcf-model` / `lbo-model` / `3-statement-model` / `comps-analysis` skill matching the request type (`model-builder.md:21`).
3. Orchestrator dispatches `model-builder-builder` → writes `./out/model.xlsx` via `xlsx-author`, executes Python via Bash for valuations (`builder.yaml:5-7,15`).
4. Orchestrator dispatches `model-auditor` → re-checks ties, balances, hardcodes (`model-builder.md:22`, `auditor.yaml:4-7`).
5. Orchestrator calls `audit-xls` skill (`model-builder.md:22`).
6. Sensitivities built (`model-builder.md:23`).
7. **Two human-review gates** — after build, after audit (`model-builder.md:30`).

### 7.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | N/A |
| Rule 204-2 | Gap; model files are work product — retention applies |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | Acceptable; ticker only |
| Prompt injection | **Low** — no untrusted-doc reader; all inputs from MCPs |
| **Bash-execution surface** | **New for this agent** — `builder.yaml:15` enables Bash in writer subagent. Phase 3 must require sandboxed-Python attestation (no internet, no filesystem outside `./out/`, no subprocess to system Python with vendor SDKs). |

### 7.5 CFA V(A) flags (Emerald-relevant)

- **Hardcoded assumption provenance** — `model-builder.md:29` requires `[ASSUMPTION]` labels in cells but no external assumption-set archive; required for V(A).
- **Survivorship in `comps-analysis`** — same as `pitch-agent` and `market-researcher`.
- **Bash-via-Python for WACC / IRR** — reproducibility requires capturing the Python invocation + numpy/scipy versions; not currently logged.

---

## 8 · `gl-reconciler`

### 8.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Reconciles general ledger to subledger across asset classes for a trade date — finds breaks, traces root cause, and routes the exception report for sign-off." | `gl-reconciler.md:3` |
| System prompt | `plugins/agent-plugins/gl-reconciler/agents/gl-reconciler.md:1-33` | full file |
| Inputs | Trade date + asset-class list | `gl-reconciler.md:11,19`, `steering-examples.json` |
| Outputs | Exception report `./out/<...>.xlsx` | `managed-agent-cookbooks/gl-reconciler/README.md:29-31` (described prose) |
| MCP egress | **internal-gl, subledger** (firm systems) | `managed-agent-cookbooks/gl-reconciler/agent.yaml:36-42` |

### 8.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `gl-reconciler-reader` | **Yes** (counterparty/custodian statements) | read, grep | none | yes (`reader.yaml:35-58`) | `reader.yaml:1-58` (canonical reader pattern) |
| `gl-reconciler-critic` | No | read, grep | internal-gl, subledger | no | `critic.yaml:1-20` |
| `gl-reconciler-resolver` (Write-holder) | No | read, write, edit | none | no | `resolver.yaml:1-18` |

### 8.3 Data flow

1. Orchestrator pulls GL+subledger balances (`gl-reconciler.md:19`).
2. Orchestrator dispatches `gl-reconciler-reader` per asset class → schema-validated breaks JSON (`gl-reconciler.md:20`, `reader.yaml:11-15`).
3. Orchestrator iterates breaks for root-cause classification (`gl-reconciler.md:21`).
4. Orchestrator dispatches `gl-reconciler-critic` → independent re-verify against trusted GL+subledger (`gl-reconciler.md:22`, `critic.yaml:4-7`).
5. Orchestrator dispatches `gl-reconciler-resolver` → assembles exception report (`resolver.yaml:5-7`).
6. **Explicit "no ledger posting" invariant** — agent produces report only (`gl-reconciler.md:29`).

### 8.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | N/A — internal accounting |
| Rule 204-2 | Reconciliation reports must be retained per recordkeeping rule |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | None — only firm-internal MCPs |
| Prompt injection | **Material** — counterparty/custodian statements are externally authored; canonical defense pattern is here (cite §2.3, §2.4). |

### 8.5 CFA V(A) flags

- Lower V(A) surface than research agents — this is operational not analytical.
- Phase 3 should still require capturing trade-date + asset-class list +
  break-set hash for reproducibility.

---

## 9 · `kyc-screener`

### 9.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Parses an onboarding document packet, runs the firm's KYC/AML rules engine, screens against sanctions and PEP lists, and flags gaps for escalation." | `kyc-screener.md:3` |
| System prompt | `plugins/agent-plugins/kyc-screener/agents/kyc-screener.md:1-33` | full file |
| Inputs | Onboarding packet ID | `kyc-screener.md:11,20` |
| Outputs | `./out/escalation-<packet>.xlsx` | `managed-agent-cookbooks/kyc-screener/README.md:29` |
| MCP egress | screening (third-party — receives party names + identifiers) | `agent.yaml:17-20` |

### 9.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `kyc-doc-reader` | **Yes** (passports, formation docs, UBO charts) | read, grep | none | yes (`doc-reader.yaml:17-37`) | `doc-reader.yaml:1-37` |
| `kyc-rules-engine` | No | read, grep | screening | no | `rules-engine.yaml:1-18` |
| `kyc-escalator` (Write-holder) | No | read, write, edit | none | no | `escalator.yaml:1-18` |

### 9.3 Data flow

1. Orchestrator dispatches `kyc-doc-reader` → schema-validated entity+UBO JSON (`kyc-screener.md:20`, `doc-reader.yaml:4-7`).
2. Orchestrator dispatches `kyc-rules-engine` → firm rules + sanctions/PEP via screening MCP (`kyc-screener.md:21-22`, `rules-engine.yaml:4-7`).
3. Orchestrator dispatches `kyc-escalator` → assembles compliance packet (`escalator.yaml:5-7`).
4. **No risk-rating decision** — agent recommends; compliance officer decides (`kyc-screener.md:29`).

### 9.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| **Reg S-P 2024 customer info** | **Acute hardening required** — onboarding documents are NPI by definition; doc-reader output (entity name, country, UBO names + percentages) is sensitive customer information. |
| **AML recordkeeping** | RIA AML rule (effective 2026) imposes specific retention requirements distinct from Rule 204-2; Phase 3 must specify both schemes. |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| **Vendor egress (screening MCP)** | Intentional egress of party names; vendor attestation + DPA review required. |
| Prompt injection | **Material** — adversarial onboarding documents could attempt to coerce the rules engine; defense per §2.3, §2.4. |

### 9.5 CFA V(A) flags

- N/A directly — this is an operations agent, not analytical.
- Suitability-adjacent: rules-engine pass/fail directly influences client
  acceptance. Phase 3 must require firm to validate rule set against actual
  written KYC policy, not against the demo rules.

---

## 10 · `valuation-reviewer`

### 10.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Ingests GP valuation packages for a fund, runs them through the valuation template, and stages LP reporting." | `valuation-reviewer.md:3` |
| System prompt | `plugins/agent-plugins/valuation-reviewer/agents/valuation-reviewer.md:1-31` | full file |
| Inputs | Fund + as-of date | `valuation-reviewer.md:11,19` |
| Outputs | `./out/lp-pack-<fund>.xlsx` | `managed-agent-cookbooks/valuation-reviewer/README.md:29` |
| MCP egress | portfolio (firm-internal) | `agent.yaml:17-20` |

### 10.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `valuation-package-reader` | **Yes** (GP packages) | read, grep | none | yes (`package-reader.yaml:17-33`) | `package-reader.yaml:1-33` |
| `valuation-runner` | No | read, grep | portfolio | no | `valuation-runner.yaml:1-18` |
| `valuation-publisher` (Write-holder) | No | read, write, edit | none | no | `publisher.yaml:1-18` |

### 10.3 Data flow

1. Orchestrator dispatches `valuation-package-reader` → schema-validated portco-mark JSON (`valuation-reviewer.md:19`).
2. Orchestrator calls `returns-analysis` + `portfolio-monitoring` skills (`valuation-reviewer.md:20`).
3. Orchestrator dispatches `valuation-runner` → marks-vs-policy via portfolio MCP, runs waterfall (`valuation-runner.yaml:4-6`).
4. Orchestrator dispatches `valuation-publisher` → assembles LP pack (`publisher.yaml:5-7`).
5. **No external distribution** — IR + CCO sign-off outside agent (`valuation-reviewer.md:27`).

### 10.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | LP capital-account info is NPI for LPs who are individuals; Reg S-P applies to LP-side outputs. |
| Rule 204-2 | Valuation reviews are advisory work product — retention applies. |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | None — firm-internal portfolio MCP only |
| Prompt injection | **Material** — GP packages are external; defense per §2.3, §2.4 |

### 10.5 CFA V(A) flags

- **Mark-to-policy variance threshold** — `valuation-runner` flags variances; Phase 3 must specify Emerald's actual policy threshold.
- **Waterfall reproducibility** — fee/carry calculations must be archived with input snapshot.

---

## 11 · `month-end-closer`

### 11.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Runs the month-end close for an entity — accruals, roll-forwards, and variance commentary — and stages the close package for controller sign-off." | `month-end-closer.md:3` |
| System prompt | `plugins/agent-plugins/month-end-closer/agents/month-end-closer.md:1-32` | full file |
| Inputs | Entity + period (YYYY-MM) | `month-end-closer.md:11,20` |
| Outputs | `./out/close-package-<entity>-<period>.xlsx` | `managed-agent-cookbooks/month-end-closer/README.md:29` |
| MCP egress | internal-gl (firm-internal) | `agent.yaml:17-20` |

### 11.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `close-ledger-reader` | **Yes** (vendor invoices, vendor statements) | read, grep | none | yes (`ledger-reader.yaml:17-33`) | `ledger-reader.yaml:1-33` |
| `close-rollforward` | No | read, grep | internal-gl | no | `rollforward.yaml:1-17` |
| `close-poster` (Write-holder) | No | read, write, edit | none | no | `poster.yaml:1-18` |

### 11.3 Data flow

1. Orchestrator pulls trial balance (`month-end-closer.md:20`).
2. Orchestrator dispatches `close-ledger-reader` → schema-validated invoice support JSON (`ledger-reader.yaml:4-7`).
3. Orchestrator dispatches `close-rollforward` → accrual + roll-forward schedules + variance commentary via internal-gl (`rollforward.yaml:4-6`).
4. Orchestrator dispatches `close-poster` → close package, never posts to GL (`poster.yaml:5-7`).
5. **No GL posting** — JE drafts only (`month-end-closer.md:28`, `poster.yaml:7`).

### 11.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | N/A — internal accounting |
| Rule 204-2 | Close packages must be retained |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | None |
| Prompt injection | **Material** — vendor invoices/statements are externally authored; defense per §2.3, §2.4 |

### 11.5 CFA V(A) flags

- N/A directly — operational.
- Phase 3 should require Emerald to test the never-post invariant
  (`poster.yaml:7`) with an explicit unit test; the invariant is prose-only.

---

## 12 · `statement-auditor`

### 12.1 Profile

| Field | Value | Cite |
|---|---|---|
| **Purpose** | "Audits a batch of pre-generated LP capital-account statements against the fund NAV pack before distribution — ties out balances, allocations, and fees, and flags discrepancies." | `statement-auditor.md:3` |
| System prompt | `plugins/agent-plugins/statement-auditor/agents/statement-auditor.md:1-30` | full file |
| Inputs | Statement batch ID + fund NAV pack | `statement-auditor.md:11,19` |
| Outputs | `./out/signoff-<batch>.xlsx` | `managed-agent-cookbooks/statement-auditor/README.md:29` |
| MCP egress | nav (firm-internal) | `agent.yaml:17-20` |

### 12.2 Subagent trust tiers

| Subagent | Untrusted? | Tools | MCPs | output_schema | Cite |
|---|:---:|---|---|:---:|---|
| `stmt-statement-reader` | **Yes** (pre-generated LP statements) | read, grep | none | yes (`statement-reader.yaml:17-33`) | `statement-reader.yaml:1-33` |
| `stmt-reconciler` | No | read, grep | nav | no | `reconciler.yaml:1-17` |
| `stmt-flagger` (Write-holder) | No | read, write, edit | none | no | `flagger.yaml:1-18` |

### 12.3 Data flow

1. Orchestrator dispatches `stmt-statement-reader` → per-LP schema-validated balance JSON (`statement-auditor.md:19`).
2. Orchestrator dispatches `stmt-reconciler` → field-by-field tie-out vs. nav MCP (`reconciler.yaml:4-6`).
3. Orchestrator dispatches `stmt-flagger` → exception list + sign-off sheet (`flagger.yaml:5-7`).
4. **Pass/hold recommendation; IR distributes after sign-off** (`statement-auditor.md:26`).

### 12.4 Compliance bucket: **(b)**

| Dimension | Verdict |
|---|---|
| Reg S-P 2024 | LP statement contents include LP-specific NAV/contrib/distrib — NPI for individual LPs |
| Rule 204-2 | Statement-audit work-paper retention applies |
| §204A / §15(g) | Gap |
| Cowork prohibition | Hardening — CMA only |
| Vendor egress | None |
| Prompt injection | **Material** — statements are "pre-generated by an upstream system you don't control" (`statement-auditor.md:19`); defense per §2.3, §2.4 |

### 12.5 CFA V(A) flags

- **Tie-out source-of-truth** — NAV pack is authoritative; statements are the
  audited artifact. Phase 3 must specify NAV pack provenance + lock at
  audit-time.

---

## 13 · Phase 2 verification gate

Run at end of phase: confirm every system-prompt + subagent line-range
citation in §3–§12 resolves to an actual file/range at SHA `bb4a2b3...`,
and that the path-lockdown invariant holds. See the phase-complete banner
immediately following this document.
