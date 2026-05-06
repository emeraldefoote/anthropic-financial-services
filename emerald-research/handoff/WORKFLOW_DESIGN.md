# WORKFLOW_DESIGN.md — How to chain these for analyst time savings

> **What this is.** Worked examples of Emerald-style analyst workflows
> reconstructed around the FSI agents. Each example shows the chain
> (steering events → handoff edges → outputs), the §204-2 archive points,
> the human-approval gates, and a qualitative time-savings estimate.
>
> **The unit of value.** Time saved per analyst per week, on workflows
> that already happen — not net-new outputs, just faster paths to the
> same deliverable.

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

## §2 · Worked example: earnings week (current vs proposed)

### §2.1 · Status quo

For a 30-name coverage list, when Q-end earnings season hits, an Emerald
analyst's typical week looks like this (estimated; refine against actual
firm data):

| Day | Activity | Hours per analyst |
|---|---|---:|
| Mon | Pre-earnings setup, scenario tables for the 6–8 names reporting that week | 4 |
| Tue–Fri | Per-name (assume 6–8 names report): pull transcript, read 10-Q/8-K, drop actuals into model, roll estimates, draft note | 4 × 8 = ~32 |
| Fri | Variance commentary, morning-note recap | 3 |
| **Total** | | **~39 hours** |

Most of those 32 hours is mechanical: transcript reading, actuals dropping,
model rolling, variance flagging. The analyst's *judgment* is concentrated
in the thesis-update + estimate-revision moments.

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

### §2.3 · Estimated time saved

| Step | Status quo (analyst) | Proposed (analyst supervises) | Savings |
|---|---:|---:|---:|
| Transcript reading + actuals extraction | 1.5h × 7 names | 0.4h × 7 (review reader output) | ~7.5h |
| Model rolling | 1h × 7 names | 0.3h × 7 (review delta log) | ~5h |
| Variance commentary | 0.5h × 7 | 0.1h × 7 | ~3h |
| Note draft | 1h × 7 | 0.4h × 7 (mark up draft) | ~4h |
| **Total per analyst per earnings week** | **~32h** | **~12h** | **~20h saved** |

Caveats:
- Numbers are illustrative; refine against actual Emerald analyst time data.
- Savings only realized after Emerald has built the eval suite (V(A)
  diligence) and analysts trust the agent outputs enough to operate in
  supervise-and-approve mode rather than re-do mode.
- The first 2–3 earnings weeks under this workflow probably *cost* time
  while analysts learn what to trust. Realistic break-even: quarter 2 of
  pilot.

### §2.4 · §204-2 archival points

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
plus 3–5 ideas that best express a working theme. Analyst spends 4–6
hours pulling sector data, drafting an overview, building comps, and
listing names.

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

### §3.3 · Time saved

Status quo: ~5 hours analyst.
Proposed: ~1.5 hours (review primer, refine universe boundary,
mark up note-writer output).
**Net: ~3.5 hours/weekly primer.**

### §3.4 · V(A) checkpoint

The `idea-generation` skill (used inside `market-researcher`) defaults to
a current-listed CapIQ universe — survivorship-biased per
`EMERALD_ADAPTATION.md` §2.2.1. **Mandatory** before this workflow goes
live: replace the universe input with an Emerald-controlled universe that
backfills delisted names. Document the universe-construction rule for
V(A) reasonable basis.

---

## §4 · Worked example: client meeting prep (Emerald Advisors arm)

### §4.1 · Status quo

Advisor preparing for a quarterly client meeting: pull holdings, review
recent activity in CRM, scan news touching the client's portfolio, draft
talking points and a suggested agenda. ~45-60 min per meeting.

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

### §4.3 · Time saved + risk

- Time saved: ~30 min/meeting × meetings/week.
- **Reg S-P 2024 risk**: pack contents are NPI; egress proxy + advisor
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

**Time saved:** ~6 hours/quarter on a 30-name coverage list.

**Risk profile:** low — public filings only, no client NPI. Standard
204-2 retention applies.

---

## §6 · Day-in-the-life — proposed analyst Tuesday during earnings week

A concrete-as-possible sketch of how an Emerald analyst's day reshapes:

```
07:00  Morning brief (existing process — unchanged)

07:30  REVIEW overnight earnings-reviewer outputs (3 names reported overnight)
       Agent has produced for each:
         - ./out/model-TICKER.xlsx  (actuals dropped, estimates rolled)
         - ./out/note-TICKER.docx   (variance + read-through draft)
         - §204-2 archive row pending approval
       
       Analyst spends ~15 min per name reviewing the variance table and
       reading-the-call summary. Approves model + marks up note draft.
       Approval action is the typed-tool-call gate; archive row updates.

09:00  Morning meeting (existing — uses morning-note skill output as input,
       unchanged)

09:30  Three more names reporting today; analyst kicks off earnings-reviewer
       fan-out (one CMA invocation per name). Workflow engine schedules
       ~45 min per name; analyst returns at noon to review the first two.

10:00  PM asks for a fresh primer on energy-services consolidation theme.
       Analyst kicks off market-researcher. Returns to do other work.

12:00  Review market-researcher output: primer draft + 5-name idea shortlist.
       Marks up. Picks 2 names for deeper modeling. Triggers 
       handoff_request → model-builder for each.

14:00  Reviews 11am earnings-reviewer outputs (the first two of the 
       afternoon-reporting names). Approves both.

15:30  model-builder outputs land for the 2 marked-up names. Analyst
       reviews the auditor's pass/fail report, approves models.

16:00  Last name of the day reports. Analyst kicks off earnings-reviewer.

16:45  Review final name's output. Approve. End of day.

[~3 hours of focused review work replaced what would have been ~10 hours
of mechanical extraction + model rolling.]
```

**The shift in analyst role:** from doer to supervisor + judgment-applier.
The agent does the mechanical work; the analyst spends time on the
high-value judgment moments (thesis update, estimate revision, idea
selection).

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

---

## §8 · Phased rollout proposal

A defensible 3-quarter rollout for Emerald:

### Q1 · Foundation (no production agent yet)

- Build the §1.1 archive store + §1.2 approval-gate harness.
- Build the §1.5 vendor-egress proxy.
- Build the §1.6 eval framework + initial eval set for `earnings-reviewer`.
- Pilot `earnings-reviewer` against 3–5 historical earnings events with
  archived golden truth. Measure variance-table accuracy + note-draft
  quality. Cost: platform engineering + 2 analysts × 50% time × 13 weeks.

### Q2 · First production agent

- Production-deploy `earnings-reviewer` for 3–5 covered names.
- Track: time saved, accuracy, false flag rate, analyst approval
  rate, archive completeness audits.
- Concurrently: build eval set for `model-builder`; pilot it.
- Author first Emerald-specific agent (suggest `coverage-monitor` or
  `13F-tracker` — neither involves NPI; both have low Reg S-P risk).

### Q3 · Expansion

- Production-deploy `model-builder` and `market-researcher` (after
  survivorship-corrected universe is wired).
- Production-deploy first Emerald-authored agent.
- Begin Reg S-P review for `meeting-prep-agent` if Emerald Advisors arm
  decides to pilot it.
- Conduct mid-year V(A) review: agents in production vs. analyst time
  saved vs. error rate.
