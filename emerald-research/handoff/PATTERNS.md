# PATTERNS.md — Architectural patterns to learn from this repo

> **What this is.** The 10 reusable patterns the Anthropic FSI repo embeds.
> Each is more valuable than any single agent because Emerald can apply it
> to firm-specific agents we build on top.
>
> **Why this matters.** The repo's agents are reference templates; the
> *patterns* are what make those templates safe, auditable, and composable.
> Internalize the patterns and Emerald can author production-quality agents
> ourselves.

---

## P1 · Three-tier isolation (Reader → Critic/Runner → Writer)

**The pattern.** Every agent that ingests untrusted documents splits its work
across three subagents:

```
┌───────────────────────────────────────────────────────────────────────┐
│ Orchestrator (read-only: Read/Grep/Glob + read-only firm/vendor MCPs) │
└─────┬─────────────────┬─────────────────┬─────────────────────────────┘
      │                 │                 │
      ▼                 ▼                 ▼
┌──────────┐     ┌──────────────┐    ┌────────────┐
│  Reader  │     │ Critic /     │    │   Writer   │
│          │     │ Runner /     │    │            │
│ (UNTRUSTED      │ Engine       │    │            │
│  ingestion)│   │ (re-verify   │    │ (file out) │
│          │     │  via trusted │    │            │
│ Read+Grep│     │  MCP)        │    │ Read+Write │
│          │     │              │    │ +Edit      │
│ no MCP   │     │ Read+Grep +  │    │            │
│ no Write │     │ vendor/firm  │    │ no MCP     │
│          │     │ MCP          │    │ no untrust │
│ schema-  │     │              │    │ ingestion  │
│ validated│     │ no Write     │    │            │
│ JSON out │     │              │    │            │
└──────────┘     └──────────────┘    └────────────┘
```

**Where in repo.** 8 of 10 agents follow this exactly: `gl-reconciler`,
`market-researcher`, `earnings-reviewer`, `meeting-prep-agent`,
`kyc-screener`, `valuation-reviewer`, `month-end-closer`, `statement-auditor`.

**The 2 exceptions** (`pitch-agent`, `model-builder`) skip the reader tier —
their inputs come from MCP-vended trusted vendor data only, no untrusted
documents enter the workflow.

**Why it works.**
- The reader is the only tier that touches the threat surface (untrusted
  documents). It has no Write, no MCPs, no callable_agents — minimal blast
  radius if it's coerced.
- The critic re-verifies against trusted internal MCPs before anything
  reaches the writer. Independent confirmation = §204A "reasonably designed".
- The writer is the only worker with `Write/Edit` and never opens untrusted
  content. Even if upstream is compromised, the writer cannot be coerced
  into reading attacker-controlled bytes.

**Emerald reuse.** Any agent we build that ingests vendor-provided documents
(LP statements, custodian feeds, GP reports, regulatory filings) inherits
this shape automatically. **Default to this pattern unless you can prove
inputs are MCP-vended and trusted.**

---

## P2 · Schema-validated reader output (length cap + character-class whitelist)

**The pattern.** Every reader subagent declares an `output_schema:` block
that constrains its JSON output via:

1. **Length caps** — `maxLength: 32` on every string, `maxItems: 500` on
   every array.
2. **Character-class whitelists** — `pattern: "^[A-Za-z0-9 .,%$()_/:-]+$"`
   on free-text fields. **Excludes shell metachars (`$()`, backticks, `&&`),
   markdown code fences, angle brackets `<>`, curly braces `{}`, newlines.**

The schema is enforced by `scripts/validate.py` between the reader and the
orchestrator; failures discard the output before the orchestrator ever sees
it.

**Why it works.** Even if the reader's prompt is overcome by an injected
instruction in the source document, the *output* cannot survive intact
through the schema gate. An attacker who wants to coerce the orchestrator
needs to (a) write the injection in a way the reader will faithfully
transcribe, AND (b) survive the regex whitelist. The intersection is
nearly empty.

**Example whitelist regexes from the repo:**

| Field | Pattern | Excluded |
|---|---|---|
| `account` | `^[A-Za-z0-9._:-]+$` | spaces, every shell metachar |
| `claim` (sector facts) | `^[A-Za-z0-9 .,%$()_/&:-]+$` | backticks, `<>`, `{}`, newlines |
| `ticker` | `^[A-Z.]+$` | extreme: only uppercase + dot |
| `period` | `^[0-9]{4}-[0-9]{2}$` | extreme: only `YYYY-MM` |
| `country` | `^[A-Z]{2}$` | extreme: only ISO-2 |

**Emerald reuse.** When authoring a new reader, **always declare an
output schema**. Make the regex as restrictive as the field's domain
allows. If a field is "free narrative", make it short (`maxLength: 256`)
and exclude HTML/markdown/shell metachars at minimum.

---

## P3 · Allowlist + payload-validated cross-agent handoffs

**The pattern.** Agents never call each other via `callable_agents`. Instead:

1. Source orchestrator emits a `handoff_request` JSON blob in its **text
   output**.
2. The orchestration layer (`scripts/orchestrate.py` reference impl) extracts
   the blob via regex.
3. Validates `target_agent` against a hard-coded **10-name allowlist**.
4. Validates `payload` against a strict jsonschema (`event` ≤ 2000 chars,
   `context_ref` matches `^[A-Za-z0-9 ._/:#-]+$`).
5. Only after validation does the handoff become a new steering event to
   the target agent.

**Why this is a security pattern, not a convenience pattern.** Handoff text
is emitted *downstream of untrusted-document readers*. An attacker who
controls a processed document could embed a literal `handoff_request` blob
attempting to coerce a flow. The allowlist + schema validation are the rails
that block it.

**The repo's own warning** (from `scripts/orchestrate.py:11-14`): "In
production, prefer emitting handoffs via a dedicated tool call or a typed
SSE event the model cannot produce by quoting document text." The text-echo
pattern is documented as a reference, not an endorsement.

**Documented handoff edges in the repo:**
- `pitch-agent` → `model-builder` (rebuild after thesis change)
- `market-researcher` → `model-builder` (model an idea-shortlist name)
- `earnings-reviewer` → `model-builder` (rebuild DCF after earnings)
- `gl-reconciler` → `month-end-closer` (verified breaks fold into close)
- `valuation-reviewer` → `gl-reconciler` (flagged portcos)

**Emerald reuse.** When chaining Emerald agents, use a typed-tool-call
channel from day one. Don't echo handoffs through model output text. If you
must, run them through an allowlist + jsonschema gate identical in spirit
to the reference impl.

---

## P4 · All MCPs are read-only by default

**The pattern.** Every MCP toolset declared in every agent.yaml has its
`default_config` annotated `# read-only server`. Cite:
`managed-agent-cookbooks/gl-reconciler/agent.yaml:30,34`.

**Why it works.** An agent cannot mutate firm or vendor systems. Worst case
on prompt injection: reader of false data, writer of mis-formatted output.
The agent cannot post to the GL, modify CRM, place a trade, or send mail.

**Emerald reuse.** **Every Emerald MCP must default to read-only.** Anything
that mutates state (place a trade, mark up a model) belongs in a separate,
human-gated workflow outside the agent surface — never wire a write-capable
MCP to an agent.

---

## P5 · Single Write-holder per agent

**The pattern.** Of 3 subagents per agent, exactly 1 has `Write`. The others
have `Read` only. The README files explicitly **bold** the Write-holder:

| Agent | Write-holder |
|---|---|
| pitch-agent | **deck-writer** |
| market-researcher | **note-writer** |
| earnings-reviewer | **note-writer** |
| meeting-prep-agent | **pack-writer** |
| model-builder | **builder** |
| gl-reconciler | **resolver** |
| kyc-screener | **escalator** |
| valuation-reviewer | **publisher** |
| month-end-closer | **poster** |
| statement-auditor | **flagger** |

**The Write-holder's prompt always includes** "You are the ONLY worker with
Write" and "Never open [untrusted source] directly." The instruction is
prose-level reinforcement; the architecture (no MCPs in writer subagent)
is the actual enforcement.

**Why it works.** Audit becomes localized. If a file lands in `./out/` that
shouldn't have, exactly one subagent could have written it. Combined with
P4 (read-only MCPs), the writer cannot egress data to any third-party
system either.

**Emerald reuse.** When authoring new agents, give exactly one subagent
`Write`. If you need multiple output formats, the same writer produces all
of them — don't fan Write across multiple subagents.

---

## P6 · Plugin + cookbook duality (one source, two surfaces)

**The pattern.** Every named agent ships in two forms from one source:

```
plugins/agent-plugins/<slug>/                 ← Cowork plugin form
├── .claude-plugin/plugin.json
├── agents/<slug>.md         ← canonical system prompt (one source)
└── skills/                  ← bundled skills (vendored from verticals)

managed-agent-cookbooks/<slug>/               ← CMA cookbook form
├── agent.yaml               ← references ../../plugins/.../agents/<slug>.md
├── subagents/*.yaml         ← three depth-1 leaf workers
├── steering-examples.json
└── README.md                ← security tier + handoff notes
```

The `agent.yaml` references the same canonical `agents/<slug>.md` as the
Cowork plugin. **System prompt drift between Cowork and CMA is impossible
by construction.**

**The Cowork frontmatter `tools:` line and the CMA `agent_toolset` *do*
diverge** (Cowork allows Write/Edit on the orchestrator; CMA strips them
to the writer subagent). This is intentional — Cowork is interactive and
benefits from orchestrator Write; CMA is headless and benefits from
trust-tier isolation.

**Emerald reuse.** Even though Emerald uses CMA only, **author both
manifests**. The Cowork plugin form documents the agent; the CMA cookbook
form deploys it. Maintaining both keeps the design self-documenting.

---

## P7 · Skills are the source of truth; agents vendor copies

**The pattern.** Skill content lives at
`plugins/vertical-plugins/<v>/skills/<name>/SKILL.md` (single source).
Agents that bundle a skill have a vendored copy at
`plugins/agent-plugins/<slug>/skills/<name>/SKILL.md`. The vendoring is
performed by `scripts/sync-agent-skills.py`.

**Why two copies?** Cowork plugins are self-contained — installing
`pitch-agent` on its own should give the user every skill it needs without
also requiring `financial-analysis`. The vendored copies make the agent
plugin standalone.

**The check.** `scripts/check.py` lints for drift — if any agent-bundled
skill has diverged from its vertical source, the check fails. **Edit at
the vertical, run sync, never edit the bundled copy.**

**Emerald reuse.** Same model. Author firm skills under
`<emerald-fork>/plugins/vertical-plugins/emerald-research/skills/` and
sync into the agent bundles. Don't fork the bundled copies.

---

## P8 · Headless authoring infrastructure (xlsx-author / pptx-author)

**The pattern.** Two infrastructure skills (`xlsx-author`, `pptx-author`)
exist *because Managed Agents run headless* (no live Office app). They
produce `.xlsx` / `.pptx` files on disk via Python (openpyxl / python-pptx).

In Cowork or Office-add-in mode, the same agent would drive a live
workbook via Office JS. The skills (e.g. `dcf-model`) branch on environment
at the top:

```text
**Environment: Office JS vs Python/openpyxl:**
- If running inside Excel (Office Add-in / Office JS environment): Use Office JS directly...
- If generating a standalone .xlsx file (no live Excel session): Use Python/openpyxl as described below...
```

**Emerald reuse.** Standardize on the headless openpyxl path for CMA
deployment — it's reproducible, version-pinnable, and survives §204A audit
because the artifact-generation steps are deterministic Python, not opaque
Office automation.

---

## P9 · Steering examples as test inputs

**The pattern.** Every cookbook ships `steering-examples.json` with 2–4
example invocations:

```json
[
  { "event": "Reconcile GL vs subledger, trade date 2026-04-30, classes: equities, fixed-income, derivatives",
    "description": "Daily run across three asset classes" },
  { "event": "Re-trace break: account 41200-EQ-US, trade date 2026-04-30",
    "description": "Follow-up steering event to deep-dive a single break" }
]
```

**Why they matter.** These are the agent's "happy-path test cases".
The format is short, structured strings (not free-form documents) — which
is itself a defense (P3): a steering event is too short to carry a
malicious payload, and the agent's behavior on each example is something
you can eval against.

**Emerald reuse.** When authoring a new agent, write the steering examples
*first* — they force you to articulate exactly what trigger phrases and
shapes the agent should accept. Use Emerald-synthetic identifiers
(`EMRD-COVERAGE-001` not `NVDA`) so analysts don't accidentally run real
production names against unhardened agents.

---

## P10 · "Stop and surface for review" as the human-in-the-loop primitive

**The pattern.** 6 of 10 agent system prompts include explicit
"Stop and surface for review" language at named workflow checkpoints
(e.g. after Excel build, after deck generation, after note draft).

**Caveat — the gap.** The "stop" is **prose-only**. There is no tool gate
that actually halts execution. A purely autonomous CMA invocation will
not pause; it will run end-to-end and produce all artifacts.

**Emerald reuse.** Replace the prose-only stop with a typed
`request_human_approval` tool call (per EMERALD_ADAPTATION.md §1.2). The
harness intercepts the call, blocks until a named human responds via
Emerald's approval UI, then resumes. The human-approval moment is logged
to the §1.1 archive.

---

## Pattern dependencies (what stacks on what)

```
                          P10 (human-in-loop)
                              │
                          P3 (handoff allowlist) ◄── P1 (3-tier)
                              │                      │
                              ▼                      ▼
P9 (steering)  ──────────►  P1 (3-tier isolation)
                              │     │     │
                              ▼     ▼     ▼
                         Reader  Critic  Writer
                              │     │     │
                              │     │     │
                          P2 (schema)  P4 (RO MCP)  P5 (single Write)
                              │
                              ▼
                          P7 (skills vendoring)
                              │
                              ▼
                          P8 (headless authoring)
                              │
                              ▼
                          P6 (plugin/cookbook duality)
```

The whole thing is self-reinforcing: weaken any single pattern and the
threat model degrades. Get all 10 right and an Emerald-authored agent
inherits the same defenses as the Anthropic reference templates.

---

## What's *not* in the repo (patterns Emerald must add)

The following are gaps the repo does not address but Emerald must:

| Missing pattern | Why Emerald needs it | Source |
|---|---|---|
| **Rule 204-2 archival hook** — append-only log of (input, output, model, prompt-hash, mcp-set, operator, approval) tuples per invocation | SEC recordkeeping rule, 5-year-onsite + 2-year-easily-accessible | EMERALD_ADAPTATION.md §1.1 |
| **Typed human-approval tool** — replaces prose-only "stop and surface" | §204A "reasonably designed" supervision — needs an enforced gate, not narrative | EMERALD_ADAPTATION.md §1.2 |
| **Vendor-egress payload redaction proxy** — strip client identifiers before any CapIQ/FactSet/Daloopa query | Reg S-P 2024 + firm-IP protection | EMERALD_ADAPTATION.md §1.5 |
| **Per-agent eval set** — golden-path + edge-case task set, run on every model upgrade | CFA V(A) Diligence + change management | EMERALD_ADAPTATION.md §1.6 |
| **Survivorship-corrected universe construction** | CFA V(A) — current-listed-only universes are biased | EMERALD_ADAPTATION.md §3 |
| **Consensus snapshot capture** for any agent that pulls FactSet consensus | V(A) reproducibility — consensus mutates over time | EMERALD_ADAPTATION.md §2.3.1 |
