# EMERALD_ADAPTATION.md — Per-agent hardening playbook

> **Audience.** Ed Foote / Emerald platform team. This document operationalizes
> the Phase 2 compliance bucketing (`ARCHITECTURE.md` §1, sibling file) into concrete
> hardening steps for an Emerald-context deployment of the Anthropic FSI
> agents at SHA `bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d`.

> **Bucket assignment recap.** All 10 agents are bucket **(b)**. None are
> compatible out of the box (a); none are incompatible in design (c). The
> hardening below has two layers: **§1 repo-wide hooks** (uniform, apply to
> every agent) and **§2 per-agent deltas**.

> **Cowork stance.** Per operator instruction (chat, 2026-05-06): Cowork is
> *firm-prohibited* but worth understanding. This document treats the
> Cowork prohibition as a uniform deployment-channel constraint (CMA-only),
> not as a per-agent compatibility veto.

---

## §1 · Repo-wide hardening hooks (apply to all 10 agents)

These three line items are the reason every agent is bucket (b). Close them
once at the platform layer and the per-agent deltas in §2 become the only
remaining work.

### §1.1 · Rule 204-2 recordkeeping wrapper

**Gap.** SOURCE_REPO ships zero recordkeeping instrumentation. File outputs
land in `./out/` with deterministic names; no input/output archive, no
operator/timestamp/model-version capture.

**Required artifact set per CMA invocation:**

| Field | Source | Notes |
|---|---|---|
| `invocation_id` | UUID generated at orchestrate-time | Joins to all rows below |
| `agent_slug` | from `agent.yaml:3` | one of the 10 names |
| `model` | from `agent.yaml:4` | currently `claude-opus-4-7` for all |
| `model_version_pin` | Anthropic API response header | for reproducibility |
| `system_prompt_sha256` | hash of resolved system+append text | catches Anthropic upstream prompt changes |
| `mcp_servers_active` | from `agent.yaml:mcp_servers` block | URL + auth-mode |
| `steering_event_text` | the user-supplied event verbatim | up to 2000 chars per `orchestrate.py` schema |
| `started_at`, `ended_at` | ISO-8601 UTC | |
| `operator_user_id` | Emerald SSO subject claim | not the agent — the human who kicked the run |
| `output_artifact_paths` | absolute paths under `./out/` | one row per file written |
| `output_artifact_sha256` | per-file hash | |
| `human_approval_status` | one of `pending` / `approved-by-<user>-at-<ts>` / `rejected-by-<user>-at-<ts>-reason-<text>` | satisfies §204A audit-trail |
| `subagent_calls` | one row per orchestrator → subagent dispatch | name, started_at, ended_at, output_schema_validated y/n |
| `mcp_call_log` | one row per MCP tool call | server-name, tool-name, request-payload-hash, response-payload-hash |

**Implementation pattern.** Wrap `scripts/orchestrate.py` in an Emerald
fork (`emerald/orchestrate_204_2.py`) that emits these tuples to an
append-only retention store with the SEC-mandated 5-year-onsite +
2-year-easily-accessible policy. Cite the existing reference loop:
`scripts/orchestrate.py:1-37`.

### §1.2 · §204A / §15(g) "reasonably designed" supervision overlay

**Gap.** The "Stop and surface for review" guardrails in 6 of 10 system
prompts (`pitch-agent.md:32`, `market-researcher.md:32`,
`earnings-reviewer.md:24`, `model-builder.md:24,30`, `meeting-prep-agent.md:22`,
`statement-auditor.md:26`) are prose-only with no enforcement.

**Required gate.** A typed approval gate between agent output and any
downstream action (publish, distribute, post). Two patterns work:

1. **Tool-call gate.** Replace the orchestrator's text-based "stop" with a
   typed `request_human_approval` tool call that the harness intercepts.
   The harness blocks until a human responds via Emerald's approval UI.
2. **Workflow-engine gate.** Route the agent's `./out/` artifacts to a
   Temporal/Airflow workflow with an explicit human-task step. The
   workflow ID joins to the §1.1 `invocation_id`.

Either pattern produces the `human_approval_status` field needed by §1.1.

### §1.3 · Cowork-deploy ban + CMA-only deployment policy

**Gap.** The repo's primary deploy surface is Cowork (`README.md:50-56`).
Emerald firm-wide policy prohibits Cowork.

**Required policy.** Codify in Emerald platform docs that the only
permitted deploy path for these agents is CMA via
`scripts/deploy-managed-agent.sh` (or an Emerald fork thereof) targeting
`POST /v1/agents`. This is enforced organizationally, not by code. Add a
deploy-time guard that fails the deploy if any agent is configured with a
Cowork plugin manifest active.

**Per ARCHITECTURE.md §2.2:** in CMA mode, all 10 orchestrators are
read-only at the agent_toolset level. The Cowork-side `Write/Edit`
declarations in the 5 frontmatter files do **not** load in CMA, so this
ban does not lose any necessary capability.

### §1.4 · Repo-wide injection-defense regression test

**Gap.** The schema-validated reader output is the load-bearing
inbound-injection defense (ARCHITECTURE.md §2.4). No test in the repo
proves the schemas resist actual injection payloads.

**Required test suite.** For each of the 8 untrusted-document readers
(see ARCHITECTURE.md §2.3 cite list), build a fixture set of adversarial
inputs:

- Inputs containing `ignore previous instructions`, `</system>`, `<system>`,
  `you are now`, etc.
- Inputs with shell metachars: `$(...)`, `` `...` ``, `&&`, `||`, `;`
- Inputs with markdown code fences attempting to spoof structured data
- Inputs that exceed `maxLength` on every string field
- Inputs that violate `pattern` regex on every restricted-char field

**Pass condition.** The reader's schema-validated JSON output passes
through `scripts/validate.py` *or* the orchestrator never sees the
adversarial content (rejected before exit). Run as part of every CI build
that touches any `subagents/*.yaml`.

### §1.5 · Vendor-egress payload audit

**Gap.** ARCHITECTURE.md §2.7 catalogs vendor MCPs (CapIQ, FactSet, Daloopa)
that receive query payloads with firm-IP-relevant content (which names a
client holds, which sectors are being researched for which client).

**Required control.** Per-vendor DPA + per-vendor query-payload allowlist:

- CapIQ: tickers + dates + financial fields. **No client identifiers.**
  No analyst-thesis text in the query.
- FactSet: same.
- Daloopa: same.
- Morningstar / Aiera / MT Newswires / etc.: same.
- screening (kyc-screener only): party names + identifiers (intentional;
  vendor DPA + sanctions-list source-of-truth required).

**Implementation.** Wrap MCP toolsets in an Emerald MCP proxy that
strips/redacts before egress. Cite the read-only MCP design pattern in
`managed-agent-cookbooks/gl-reconciler/agent.yaml:30,34` (`# read-only
server` comments) — extend to also be `# egress-redacted`.

### §1.6 · Eval suite (CFA V(A) Diligence)

**Gap.** No formal eval suite ships in the repo (RECON.md §4.6).

**Required.** Per-agent reference task set covering golden-path + V(A)
edge cases:

- **earnings-reviewer:** 5 covered names × 4 quarters = 20 reference
  earnings events with archived consensus snapshots; pass = variance table
  matches ground truth and the note draft contains no [UNSOURCED] markers.
- **market-researcher:** 5 sector primers with delisted-name backfilled
  universes; pass = ideas shortlist excludes survivorship-biased winners
  vs. a survivorship-corrected counterfactual.
- **model-builder:** 10 DCFs against Emerald's existing analyst-built
  models; pass = enterprise-value within 5% absent assumption changes.
- Other agents: similarly tailored task sets, scoped after Emerald
  decides which agents enter production rotation.

The eval suite output joins to §1.1's `invocation_id` so model-version
upgrades (`claude-opus-4-7` → future) can be diffed against the eval set.

---

## §2 · Per-agent hardening deltas

Each subsection below lists *additional* hardening on top of §1.

### §2.1 · `pitch-agent`

**Emerald deployment recommendation: do not deploy. Document only.**

Pitch creation is IB workflow; Emerald is RIA. Out of mandate.

If a future use case emerges, hardening on top of §1:

- Bash sandbox attestation for `modeler` subagent
  (`managed-agent-cookbooks/pitch-agent/subagents/modeler.yaml:14`): no internet,
  no fs outside `./out/`, no subprocess to system Python with credential SDKs.
- Survivorship-corrected peer universe input to `comps-analysis`.
- Human-approval gate (per §1.2) at "after Excel build" and "after deck
  generation" review points (`pitch-agent.md:32`).

### §2.2 · `market-researcher`

**Emerald deployment recommendation: high-priority candidate.**
Equity research sector primers and ideas shortlists are core to Emerald
Investment Advisors deliverables.

Hardening on top of §1:

1. **Survivorship-corrected ideas universe** (CFA V(A)). Replace the
   `idea-generation` skill's CapIQ default universe with an Emerald-controlled
   query that includes delisted names from the lookback window. Document the
   universe-construction rule explicitly per V(A) reasonable basis. Cite the
   skill source: `plugins/vertical-plugins/equity-research/skills/idea-generation/SKILL.md`.
2. **Sector-reader injection-defense regression test** (per §1.4) — sector-reader
   is the highest-injection-surface subagent in the workflow because it
   ingests third-party research PDFs and issuer materials. Cite:
   `managed-agent-cookbooks/market-researcher/subagents/sector-reader.yaml:1-32`.
3. **Vendor-egress payload audit** (per §1.5) on CapIQ + FactSet — sector and
   theme strings reveal Emerald's research direction.
4. **Universe-boundary documentation requirement.** The "8–15 names that
   define the space" line (`market-researcher.md:21`) becomes an Emerald-required
   archived field per V(A).

### §2.3 · `earnings-reviewer`

**Emerald deployment recommendation: highest-priority candidate.**
Covered-name post-earnings updates are the most directly applicable agent
for Emerald's equity-research workflow.

Hardening on top of §1:

1. **Consensus snapshot capture.** At note-draft time, archive the FactSet
   consensus snapshot used. The agent currently retrieves consensus mid-run
   (`earnings-reviewer.md:19,21`) but does not externalize the snapshot.
   Emerald must add a snapshot-write step to the §1.1 archive.
2. **Coverage-model delta provenance.** Every changed cell in the coverage
   model traces to a source per `earnings-reviewer.md:21`, but the cell-level
   trace is internal to the workbook. Emerald must add an external delta log
   (cell-address, prior-value, new-value, source-citation) per V(A).
3. **Transcript-reader regression test** (per §1.4). Highest-priority
   regression test target because earnings transcripts are externally
   authored and frequently large.
4. **Reg AC and §204-2 recordkeeping for research products.** If any
   `note-<ticker>.docx` becomes published research, Reg AC certification
   plus full Rule 204-2 retention apply at the moment of publication. The
   §1.2 human-approval gate must record the publication-decision moment.

### §2.4 · `meeting-prep-agent`

**Emerald deployment recommendation: deploy only if Emerald operates an
advisor-facing wealth workflow.** If Emerald Advisors runs SMA mandates
without an advisor-meeting cadence, this agent is out of mandate.

If deployed, hardening on top of §1 — **REG S-P 2024 ACUTE**:

1. **NPI inventory.** Catalog every NPI field the CRM MCP returns
   (relationship history, holdings, recent activity, open items per
   `meeting-prep-agent.md:18`) and bind each to a Reg S-P safeguarding
   classification.
2. **CRM MCP egress controls.** No external relay; the CRM MCP must terminate
   inside Emerald's network perimeter and never proxy to a third-party.
3. **CapIQ ticker-context redaction.** When querying CapIQ for "market events
   touching the client's holdings" (`meeting-prep-agent.md:19`), the queried
   tickers leak which holdings Emerald researches for which client. Implement
   a per-query proxy that decouples the client identity from the ticker
   query.
4. **News-reader inbound-email injection-defense regression test** (per §1.4).
   Inbound client emails are an attacker-controllable input channel.
5. **Advisor mark-up gate before client contact.** Hard gate (per §1.2): no
   talking-point or briefing pack reaches a client-facing channel without
   advisor approval. The current invariant is prose-only at line 27.
6. **Reg S-P 2024 incident-response.** If a briefing pack is exfiltrated
   (sent to wrong recipient, intercepted), the new rule requires customer
   notification within 30 days. Emerald's incident-response runbook must
   cover this agent's outputs.

### §2.5 · `model-builder`

**Emerald deployment recommendation: high-priority candidate** for
DCF/comps work supporting equity research.

Hardening on top of §1:

1. **Bash-sandbox attestation for `builder`** (`managed-agent-cookbooks/model-builder/subagents/builder.yaml:15`).
   Attestation must cover: (a) no internet, (b) no fs outside `./out/`, (c) no
   subprocess to Emerald's system Python with vendor SDKs and credentials,
   (d) explicit numpy/scipy/openpyxl version pinning archived per §1.1.
2. **Assumption-set archive.** The `[ASSUMPTION]` cell labels
   (`model-builder.md:29`) are insufficient for V(A) reproducibility. Emerald
   must capture (ticker, assumption-set-JSON, model-type, model-file-sha256,
   timestamp) tuples external to the .xlsx.
3. **Survivorship-corrected comp universe** (per §2.2.1).
4. **Office-JS vs openpyxl branch determination** must be explicit at
   invocation time. Cite: `plugins/agent-plugins/model-builder/skills/dcf-model/SKILL.md:14-25`.
   Emerald should standardize on the headless openpyxl path for CMA
   reproducibility.

### §2.6 · `gl-reconciler`

**Emerald deployment recommendation: deploy only if Emerald runs in-house
fund accounting.** If Emerald Advisors uses a third-party fund admin (the
norm for small RIAs), this agent is out of scope.

Hardening on top of §1:

1. **Map `internal-gl` and `subledger` MCPs** to Emerald's actual systems
   (`managed-agent-cookbooks/gl-reconciler/agent.yaml:36-42` env vars).
2. **Never-post invariant test.** A failing test that pretends `resolver`
   yaml has gained a posting-capable MCP. Cite:
   `plugins/agent-plugins/gl-reconciler/agents/gl-reconciler.md:29` ("No
   ledger posting").
3. **Reader regression test** (per §1.4) — counterparty/custodian
   statements are the canonical injection target.
4. **Critic-vs-reader divergence telemetry.** `critic` re-verifies each
   reported break against trusted internal MCPs
   (`managed-agent-cookbooks/gl-reconciler/subagents/critic.yaml:4-7`).
   When the critic rejects a reader-reported break, Emerald should log the
   divergence — recurring divergences may signal injection attempts.

### §2.7 · `kyc-screener`

**Emerald deployment recommendation: required if RIA AML rule applies.**
Most US RIAs are covered by the FinCEN/SEC AML rule effective 2026.

Hardening on top of §1 — **NPI + AML acute**:

1. **AML-specific recordkeeping.** Distinct from Rule 204-2; FinCEN imposes
   its own retention scheme. Emerald must implement both, not one.
2. **Replace demo rules with Emerald's written KYC policy.** The
   `rules-engine` evaluates "the firm's KYC/AML rules"
   (`plugins/agent-plugins/kyc-screener/agents/kyc-screener.md:21`); the
   shipped rules are illustrative. The mapping from policy → rule yaml is an
   Emerald-side effort.
3. **Sanctions list provider attestation.** Vendor DPA + list source-of-truth
   + update cadence + false-positive escalation policy. Document for §15(g)
   (RIA AML).
4. **Doc-reader NPI handling.** The reader's output schema
   (`managed-agent-cookbooks/kyc-screener/subagents/doc-reader.yaml:17-37`)
   structures NPI (`legal_name`, `country`, `ubo[].name`, `ubo[].pct`).
   Emerald's between-subagent transmission must be encrypted and access-controlled.
5. **No-risk-rating-decision invariant gate** (per §1.2) at line 29.
   Compliance officer's approval is a hard gate, not prose.
6. **Doc-reader injection-defense regression test** (per §1.4) — adversarial
   onboarding documents are a real threat vector.

### §2.8 · `valuation-reviewer`

**Emerald deployment recommendation: deploy only if Emerald operates a
private pooled vehicle.** Out of scope for SMA-only Emerald.

If deployed, hardening on top of §1:

1. **Marks-vs-policy threshold wiring** — the agent compares reported marks
   to "the firm's valuation policy"
   (`managed-agent-cookbooks/valuation-reviewer/subagents/valuation-runner.yaml:5`).
   Emerald must wire actual policy + variance threshold.
2. **Waterfall reproducibility** — fee/carry calculations archived per §1.1
   with input snapshot. V(A) requirement.
3. **LP NPI handling** — capital-account info for individual-LP entities is
   NPI; Reg S-P safeguarding applies to publisher output.
4. **No-external-distribution invariant gate** (per §1.2). IR + CCO
   sign-off is a hard gate. Cite:
   `plugins/agent-plugins/valuation-reviewer/agents/valuation-reviewer.md:27`.
5. **Package-reader injection-defense regression test** (per §1.4) — GP
   packages are externally authored.

### §2.9 · `month-end-closer`

**Emerald deployment recommendation: deploy at corporate-accounting layer
(Emerald entity, not portfolio).**

Hardening on top of §1:

1. **Never-post invariant test** (analogous to §2.6.2) — explicit failing
   test if `poster` yaml gains posting capability. Cite:
   `plugins/agent-plugins/month-end-closer/agents/month-end-closer.md:28`,
   `managed-agent-cookbooks/month-end-closer/subagents/poster.yaml:7`.
2. **Ledger-reader injection-defense regression test** (per §1.4) — vendor
   invoices/statements are externally authored.
3. **Coordinate `GL_MCP_URL` with `gl-reconciler`** — both agents use the
   same env var.

### §2.10 · `statement-auditor`

**Emerald deployment recommendation: same as `valuation-reviewer`** —
private-fund only.

Hardening on top of §1:

1. **NAV pack lock at audit time** — provenance + sha256 capture per §1.1.
2. **LP NPI handling** (per §2.8.3).
3. **Pass/hold human override gate** (per §1.2) — IR distributes only after
   sign-off. Cite:
   `plugins/agent-plugins/statement-auditor/agents/statement-auditor.md:26`.
4. **Statement-reader injection-defense regression test** (per §1.4).

---

## §3 · Cross-cutting Phase-2 V(A) flag remediations

These flags from ARCHITECTURE.md §2.8 cut across multiple agents:

| Flag | Affects | Remediation |
|---|---|---|
| Survivorship bias in idea-generation universe | `market-researcher`, `pitch-agent`, `model-builder` | §2.2.1, §2.5.3 — universe-construction-rule documentation + delisted-name backfill |
| Look-ahead risk on backtest misuse | `earnings-reviewer`, `market-researcher`, `model-builder`, `pitch-agent` | Add explicit "do not use for backtest assembly" guardrail to Emerald-side wrapper of each agent's system prompt; verify via §1.6 eval set |
| Model-assumption provenance | `model-builder`, `pitch-agent` (via lbo+dcf) | §2.5.2 — external assumption-set archive |
| Consensus snapshot drift | `earnings-reviewer` | §2.3.1 — snapshot capture at draft time |
| Demo data realism (real public tickers in steering examples) | All agents | Replace `steering-examples.json` with Emerald-authored synthetic identifiers (e.g. `EMRD-TEST-001`) for any Emerald-deploy fork; keep upstream demos for documentation |

---

## §4 · Deferred to Phase 4

Phase 4 will produce a pytest verification suite that:

1. Re-validates every path/line citation in this document against
   SOURCE_REPO at SHA `bb4a2b3...` (string-equality check via PROMPTS_CATALOG.md).
2. Asserts no SOURCE_REPO file has been modified since Phase 1 open.
3. Asserts the Phase 3 artifact set is complete (this file, root CLAUDE.md,
   10 agent CLAUDE.md mirrors, PROMPTS_CATALOG.md, INJECTION_LOG.md).

The hardening items above are operational work for Emerald's platform
team, not Phase-4 verification scope. The verification suite confirms the
*scaffolding* is sound; the hardening is what Emerald executes against it.
