# WORKFLOW_DESIGN.md — How to chain these into Emerald deployment plans

> **What this is.** Worked plans for how Emerald-style analyst workflows
> could be reconstructed around the FSI agents. Each plan shows the chain
> (steering events → handoff edges → outputs), the §204-2 archive points,
> and the human-approval gates.
>
> **No quantitative claims.** This document deliberately avoids
> "saves X hours" or capacity-reallocation estimates. Until a pilot
> measures actual analyst behavior with these agents in production, any
> number would be speculation. CFA V(A) Diligence + §204A "reasonably
> designed" supervision both argue against putting numbers in front of
> decision-makers before evidence exists. The plan below describes how
> the workflow *changes shape*; quantification is a Q2+ pilot output.

---

## §1 · The orchestration primitives

Two ways to chain agents:

1. **Single-agent fan-out** — one steering event, one agent, **N invocations
   in parallel** (one per ticker, period, fund, etc). Pattern:
   `for ticker in coverage_list: invoke earnings-reviewer(ticker)`. Each
   invocation is independent; the workflow engine collects outputs.
2. **Multi-agent handoff** — agent A's output triggers a `handoff_request`
   to agent B. Reference impl in `scripts/orchestrate.py`. Allowlist-
   gated and payload-validated (see PATTERNS.md §P3).

The repo documents 5 multi-agent handoff edges (PATTERNS.md §P3 table).
Emerald can extend the allowlist with new edges as new agents are added.

**Both primitives require the §1.1 Rule 204-2 archive hook** (per
`EMERALD_ADAPTATION.md` §1.1) so each invocation captures (input, output,
operator, model, prompt-hash, MCPs, approval-status). Fan-out workflows
generate one archive row per invocation; handoff workflows produce one
row per agent in the chain plus a `handoff_id` joining them.

---

## §2 · Worked example: earnings week

### §2.1 · Status quo (current Emerald earnings-week shape)

For a covered name reporting in-quarter, the current analyst rhythm is
roughly:

- Pre-earnings: scenario tables, key metrics to watch, position sizing.
- Day-of: pull the transcript, read the 10-Q/8-K, drop actuals into the
  model, roll estimates, draft a variance read.
- Post-earnings: thesis update, note draft, morning-note recap.

The mechanical steps (transcript reading, actuals extraction, estimate
rolling, variance flagging) consume the bulk of analyst time during
earnings season. The judgment-heavy steps (thesis update, estimate
revision, position-sizing decision) consume the bulk of analyst *value*.

### §2.2 · Proposed earnings-week workflow (Anthropic agents + Emerald hardening)

```
Mon (T-1)
─────────
   ┌─────────────────────────────────────────┐
   │ FAN-OUT: earnings-preview skill (slash) │
   │ for each name in coverage list with     │
   │ Q-end this week                         │
   │   → bull/bear scenarios + key metrics   │
   │     prepped overnight                   │
   └────────────────┬────────────────────────┘
                    │
                    ▼
              [analyst Mon morning: review previews, refine theses]


Tue–Fri (per-name workflow, fanned out)
───────────────────────────────────────
   STEERING EVENT: "Process earnings: TICKER QX-FYZZ"
                    │
                    ▼
   ┌──────────────────────────────────────────┐
   │ earnings-reviewer (CMA)                  │
   │  ├── transcript-reader (untrusted)       │
   │  ├── model-updater (FactSet/Daloopa)     │
   │  └── note-writer (Write)                 │
   │     → ./out/model-TICKER.xlsx            │
   │     → ./out/note-TICKER.docx             │
   └────────────────┬─────────────────────────┘
                    │
                    ▼  [if thesis change is material]
   ┌──────────────────────────────────────────┐
   │ HANDOFF → model-builder                   │
   │  ├── data-puller (CapIQ/Daloopa)         │
   │  ├── builder (Write, sandbox Python)     │
   │  └── auditor (re-check)                  │
   │     → ./out/model-TICKER-rebuilt.xlsx    │
   └────────────────┬─────────────────────────┘
                    │
                    ▼
   §204-2 ARCHIVE  (per-invocation row + handoff_id linking)
                    │
                    ▼
   HUMAN-APPROVAL GATE  (typed tool call: analyst reviews + approves)
                    │
                    ▼
   PUBLISH (downstream of agent surface — outside scope)
```

### §2.3 · How the analyst's role changes shape

The shift is from doer to supervisor + judgment-applier:

| Step | Status quo | Proposed |
|---|---|---|
| Transcript reading + actuals extraction | Analyst reads + extracts | Reader subagent extracts; analyst reviews schema-validated output |
| Model rolling | Analyst updates model | model-updater subagent rolls; analyst reviews delta log |
| Variance commentary | Analyst writes flux | model-updater drafts flux; analyst marks up |
| Note draft | Analyst drafts | note-writer subagent drafts; analyst marks up |
| Thesis update | Analyst (judgment) | Analyst (judgment) — unchanged |
| Estimate revision | Analyst (judgment) | Analyst (judgment) — unchanged |
| Approval to publish | Analyst | Analyst (typed approval gate) |

**The judgment moments stay with the analyst.** What changes is the
mechanical work *upstream* of judgment.

### §2.4 · Pilot measurement plan

Quantitative claims about analyst-time impact only meaningful after
a pilot under controlled conditions. Recommended pilot measurements
(per `EMERALD_ADAPTATION.md` §1.6 + §2.3):

- **Baseline** — measure current analyst time on a representative
  earnings event under current workflow, before agent rollout.
- **Pilot** — repeat measurement after agents are in production for
  at least one full earnings cycle (typically Q2 of pilot).
- **Distinct measures** — total elapsed time, analyst review time,
  approval-cycle time, error-detection rate, post-publication revision
  rate.
- **Not the same as savings** — capacity freed must be tracked against
  what the analyst does *with* the freed time (more coverage, deeper
  research, etc.). Capacity reallocation is the policy decision, not an
  agent-output.

### §2.5 · §204-2 archival points

Each archive row captures:
- `invocation_id` (UUID)
- `agent_slug` (`earnings-reviewer` or `model-builder`)
- `model` + `model_version_pin`
- `system_prompt_sha256` (catches Anthropic upstream prompt changes)
- `mcp_servers_active` (URL + auth-mode, redacted)
- `steering_event_text` (verbatim)
- `started_at`, `ended_at` (UTC)
- `operator_user_id` (Emerald SSO subject — the human who kicked the run)
- `output_artifact_paths` + `output_artifact_sha256` per file
- `subagent_calls` (one row per dispatch — name, schema-validated y/n)
- `mcp_call_log` (one row per MCP call — server, tool, payload-hash)
- `human_approval_status` (`approved-by-<user>-at-<ts>` or rejected)
- `handoff_id` (joins to downstream invocations)

This is the foundation of §204A "reasonably designed" supervision +
Rule 204-2 retention. Required before any production use.

---

## §3 · Worked example: weekly sector primer + idea screen

### §3.1 · Status quo

Friday afternoon: PM asks for a fresh primer on a sector under review,
plus 3–5 ideas that best express a working theme. Analyst pulls sector
data, drafts an overview, builds comps, and lists names.

### §3.2 · Proposed workflow

```
   STEERING: "Primer: <sector or theme>, angle: <one-line angle>"
                    │
                    ▼
   ┌─────────────────────────────────────────┐
   │ market-researcher (CMA)                  │
   │  ├── sector-reader (UNTRUSTED 3rd-party  │
   │  │    research; SCHEMA-VALIDATED out)    │
   │  ├── comps-spreader (CapIQ/FactSet)      │
   │  └── note-writer (Write)                 │
   │     → ./out/primer-<sector>.docx          │
   │     → ./out/primer-<sector>.pptx (opt'l) │
   └────────────────┬────────────────────────┘
                    │
                    ▼ [PM picks 1-3 names from ideas shortlist]
   ┌─────────────────────────────────────────┐
   │ FAN-OUT: model-builder (one per name)   │
   │  → ./out/model-<TICKER>.xlsx (each)     │
   └────────────────┬────────────────────────┘
                    │
                    ▼
   §204-2 archive (parent + per-fan-out child rows)
                    │
                    ▼
   PM REVIEW + APPROVAL  (typed gate)
```

### §3.3 · How the role changes shape

The PM's interaction shifts from "kick off the primer + wait for next
week" to "review the primer draft + refine the universe boundary + pick
the 1–3 names that most warrant deep modeling". The analyst's role
becomes mark-up of the note-writer output rather than first-draft
authorship of every section.

### §3.4 · V(A) checkpoint — this MUST be wired before the workflow goes live

The `idea-generation` skill (used inside `market-researcher`) defaults to
a current-listed CapIQ universe — survivorship-biased per
`EMERALD_ADAPTATION.md` §2.2.1. **Mandatory** before this workflow is
used: replace the universe input with an Emerald-controlled universe that
backfills delisted names. Document the universe-construction rule for
V(A) reasonable basis.

This is non-negotiable: an ideas shortlist drawn from a survivorship-
biased universe is a defective research product, regardless of what the
agent does downstream.

---

## §4 · Worked example: client meeting prep (Emerald Advisors arm)

### §4.1 · Status quo

Advisor preparing for a quarterly client meeting: pull holdings, review
recent activity in CRM, scan news touching the client's portfolio, draft
talking points and a suggested agenda.

### §4.2 · Proposed workflow — REG S-P 2024 acute

```
   STEERING: "Briefing pack for <client-id>, meeting <event-id>"
                    │
                    ▼
   ┌─────────────────────────────────────────────────────┐
   │ meeting-prep-agent (CMA)                             │
   │                                                      │
   │   PRE-INVOKE: §1.5 EMERALD EGRESS PROXY validates    │
   │   that no client identifier reaches CapIQ            │
   │                                                      │
   │  ├── profiler (CRM + CapIQ via egress proxy)        │
   │  ├── news-reader (UNTRUSTED inbound emails)         │
   │  └── pack-writer (Write)                            │
   │     → ./out/briefing-<client>.pptx                   │
   │                                                      │
   │   POST-INVOKE: §1.1 archive, NPI-tagged             │
   └────────────────┬────────────────────────────────────┘
                    │
                    ▼
   ADVISOR APPROVAL + MARK-UP  (typed gate; pack is not
                                client-facing until advisor
                                approves)
```

### §4.3 · Posture and risk

- **Reg S-P 2024 acute** — pack contents are NPI; egress proxy + advisor
  approval gate + 30-day breach notification runbook all required before
  this enters production.
- **Talking points are suitability-adjacent** — advisor must mark up before
  any client-facing use. Hard gate, not prose.

### §4.4 · Why this is bucket (b) not (a)

The meeting-prep agent's design itself is sound (canonical 3-tier isolation,
schema-validated news-reader). What makes it bucket (b) is the *deployment
context* — Emerald must add Reg S-P 2024 controls the repo doesn't ship.

---

## §5 · Worked example: 13F-tracker (Emerald-authored, quarterly)

This is one of the candidate Emerald-authored agents from
`EXTENSION_PLAYBOOK.md` §4.3. Workflow:

```
T+15 days post quarter-end (13F deadline)
                    │
                    ▼
   STEERING (cron): "13F scan: holders <list>, quarter <YYYY-QN>"
                    │
                    ▼
   ┌─────────────────────────────────────────┐
   │ 13F-tracker (CMA, Emerald-authored)     │
   │  ├── filing-reader (UNTRUSTED 13F-HRs   │
   │  │    from EDGAR; SCHEMA-VALIDATED out) │
   │  ├── position-runner (firm portfolio    │
   │  │    MCP for our coverage names)       │
   │  └── summary-writer (Write)             │
   │     → ./out/13f-coverage-<quarter>.xlsx │
   └────────────────┬────────────────────────┘
                    │
                    ▼
   §204-2 archive
                    │
                    ▼
   PM REVIEW (typed gate) + analyst follow-up on flagged names
```

**Risk profile:** low — public filings only, no client NPI. Standard
204-2 retention applies.

**Posture shift:** quarterly 13F review becomes a delta-driven exception
report rather than a scan-everything exercise.

---

## §6 · Day-in-the-life — proposed analyst Tuesday during earnings week

A concrete-as-possible sketch of how an Emerald analyst's Tuesday during
earnings week reshapes — focused on *role* not *clock*:

```
Morning brief
  Existing process — unchanged.

Review overnight earnings-reviewer outputs
  For each name that reported overnight, the agent has produced:
    - ./out/model-TICKER.xlsx  (actuals dropped, estimates rolled)
    - ./out/note-TICKER.docx   (variance + read-through draft)
    - §204-2 archive row pending approval

  Analyst reviews variance table and read-the-call summary per name.
  Approves model + marks up note draft. Approval action is the
  typed-tool-call gate; archive row updates.

Morning meeting
  Existing — uses morning-note skill output as input. Unchanged.

Afternoon-reporting names: kick off earnings-reviewer fan-out
  Workflow engine schedules per-name CMA invocations. Analyst returns
  later to review outputs.

PM request: fresh sector primer
  Analyst kicks off market-researcher. Returns to do other work.

Review market-researcher output
  Marks up primer draft. Picks names for deeper modeling. Triggers
  handoff_request → model-builder for each.

Reviews afternoon-reporting earnings-reviewer outputs
  Per-name model + note review. Approve.

Reviews model-builder outputs for the picked names
  Reviews auditor's pass/fail report. Approves models.

End-of-day final name review
  Approve. End of day.
```

**The shift in analyst role:** from doer to supervisor + judgment-applier.
The agent does the mechanical work; the analyst spends time on the
high-value judgment moments (thesis update, estimate revision, idea
selection, position sizing).

**Whether this saves time, redistributes time, or simply changes the
shape of the work** is a question only the pilot can answer. **Do not
forecast it.**

---

## §7 · Workflow patterns NOT to use

These patterns look attractive but break the threat model:

| Anti-pattern | Why it breaks | Use instead |
|---|---|---|
| Direct callable_agents between named agents | CMA preview is depth-1 only; loses the allowlist + payload validation | Emit `handoff_request`, route via orchestrate.py-style validator |
| One agent that "does the whole earnings workflow including publication" | Concentrates blast radius; eliminates human-approval moments | Multi-agent chain with explicit approval gates between |
| Skipping the §204-2 archive on "test" invocations | Drift between "test" and "prod" invariants; auditor cannot verify the archive is exhaustive | Archive every invocation; tag-not-skip "test" runs in the archive |
| Letting the agent kick off its own follow-on invocations | Removes operator/PM from the loop; loses approval gate | Emit `handoff_request`; the workflow engine + human approval triggers the next step |
| Running multiple agents against the same artifact concurrently | Race conditions on `./out/` filename collision; non-deterministic | Serialize chained invocations through the workflow engine |
| Skipping eval runs after a model-version change | Behavior drift; V(A) Diligence violation | Re-run the eval set on every model version pin change before resuming production traffic |
| Forecasting time savings before pilot data exists | Misleads decision-makers; CFA V(A) Diligence violation; may distort capacity-allocation choices | State posture and shape changes only; measure during pilot |

---

## §8 · Phased rollout proposal

A defensible 3-quarter rollout for Emerald. **No timeline-or-budget
estimates here** — the rollout *shape* is the durable claim; effort and
duration are platform-engineering scoping work.

### Q1 · Foundation (no production agent yet)

- Build the §1.1 archive store + §1.2 approval-gate harness.
- Build the §1.5 vendor-egress proxy.
- Build the §1.6 eval framework + initial eval set for `earnings-reviewer`.
- Pilot `earnings-reviewer` against historical earnings events with
  archived golden truth. Measure variance-table accuracy + note-draft
  quality. Publish pilot results before any production traffic.
- **Establish the baseline measurement protocol** — current analyst
  time on representative earnings events. This is the only honest
  reference point against which a future "did it help?" question can
  be answered.

### Q2 · First production agent

- Production-deploy `earnings-reviewer` for a small named set of covered
  names (the pilot cohort).
- Track: accuracy, false-flag rate, analyst approval rate, archive
  completeness audits, post-publication revision rate.
- **Track but do not pre-commit to** capacity-reallocation outcomes.
  Whether freed capacity goes to broader coverage, deeper research, or
  is absorbed by review overhead is observable, not predictable.
- Concurrently: build eval set for `model-builder`; pilot it.
- Author first Emerald-specific agent (suggest `coverage-monitor` or
  `13F-tracker` — neither involves NPI; both have low Reg S-P risk).

### Q3 · Expansion

- Production-deploy `model-builder` and `market-researcher` (after
  survivorship-corrected universe is wired).
- Production-deploy first Emerald-authored agent.
- Begin Reg S-P review for `meeting-prep-agent` if Emerald Advisors arm
  decides to pilot it.
- Conduct mid-year V(A) review: agents in production vs. observed analyst
  workflow shape vs. error/revision rates. **This is the first review
  where retrospective analyst-time data is honest input.** Forward
  forecasts can begin to be made *from observed data*, not before.

---

## §9 · A note on quantification

Throughout this document, we deliberately decline to estimate "hours
saved per week" or "capacity freed". Those numbers are tempting in a
proposal because they make the case feel concrete, but:

- **They aren't measured** — they are guesses dressed up as
  estimates. Decision-makers should distinguish.
- **They mislead capacity allocation** — if a CIO commits headcount
  reduction to a forecast that doesn't materialize, the firm is worse
  off than if no commitment was made.
- **They violate V(A) Diligence** — a research firm's discipline about
  what it claims with what evidence applies internally too. We don't
  hold ourselves to a lower epistemic standard than we hold our
  research output to.
- **The honest deliverable is the workflow shape change.** If the
  shape change is sound, the operational metric (whatever it ends up
  being) will follow. If the shape change is not sound, no number
  forecast in advance will rescue it.

When the pilot produces measured data, *that* is when quantification
enters the conversation — and even then, framed as "observed during
pilot, subject to revision as scope changes" rather than as durable
forecasts.
