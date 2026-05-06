# SKILLS_INVENTORY.md

> **What this is.** A complete catalog of every skill shipped in the Anthropic
> FSI repository, organized by vertical. **Skills are the unit of domain
> knowledge** — methodology + worked examples + Excel/PowerPoint conventions
> Claude can draw on automatically. Each agent in the repo bundles a subset.
>
> **Source paths.** All vertical skills live at
> `plugins/vertical-plugins/<vertical>/skills/<skill-name>/SKILL.md`. Each
> agent vendors copies into `plugins/agent-plugins/<slug>/skills/`; vertical
> is the source of truth (`scripts/sync-agent-skills.py` propagates).

---

## Volumes

| Vertical | Skills | Lines (KB) |
|---|---:|---:|
| financial-analysis (core) | 13 | ~400K |
| equity-research | 9 | ~384K |
| investment-banking | 9 | ~176K |
| private-equity | 10 | ~104K |
| wealth-management | 6 | ~60K |
| fund-admin | 6 | ~52K |
| operations | 2 | ~20K |
| lseg (partner) | 8 | ~76K |
| spglobal (partner) | 3 | ~272K |
| **Total** | **66 unique** | **~1.5 MB** |

Skills are mostly long markdown documents (DCF skill alone is 865+ lines)
with structured sections: methodology, formula libraries, worked examples,
output conventions (color coding, named ranges), QC rules. Reading any one
SKILL.md gives Claude domain methodology equivalent to a senior associate's
written reference.

---

## §1 · financial-analysis (core, 13 skills) — modeling primitives + Excel/PowerPoint authoring

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `dcf-model` | `/dcf` | model-builder, pitch-agent | Real DCF for equity valuation. Pulls from SEC filings + analyst reports, builds cash-flow projections + WACC + sensitivity tables; Excel output with executive summary. |
| `lbo-model` | `/lbo` | model-builder, pitch-agent | Complete LBO model templates for PE transactions, deal materials, IC presentations. Validates calcs and enforces formatting standards. |
| `comps-analysis` | `/comps` | model-builder, pitch-agent, market-researcher | Institutional-grade comparable-company analyses with operating metrics, valuation multiples, statistical benchmarking. |
| `3-statement-model` | `/3-statement-model` | model-builder, pitch-agent | Populate IS/BS/CF templates with linked statements. |
| `audit-xls` | `/debug-model` | 7 of 10 agents | Spreadsheet audit — formula accuracy, errors, BS-balance + cash tie-out + logic sanity. The repo's QC cornerstone. |
| `clean-data-xls` | — | — | Clean messy spreadsheet data — whitespace, casing, numbers-stored-as-text, dates, dupes. |
| `competitive-analysis` | `/competitive-analysis` | market-researcher | Competitive landscape decks — positioning, deep-dives, comparative analysis. |
| `deck-refresh` | — | pitch-agent | Update presentations with new numbers — quarterly refreshes, comp rolls. |
| `ib-check-deck` | — | pitch-agent | IB pitch-deck QC — number consistency across slides, narrative alignment, language polish, visual formatting. |
| `pitch-deck` (in IB vertical, but core to pitch-agent) | — | pitch-agent | (See investment-banking section.) |
| `pptx-author` | — | pitch-agent, market-researcher, meeting-prep-agent | Headless `.pptx` authoring — for managed-agent sessions with no live Office app. |
| `xlsx-author` | — | 7 of 10 agents | Headless `.xlsx` authoring — same as pptx-author but Excel. |
| `ppt-template-creator` | `/ppt-template` | — | Creates reusable PPT-template SKILLs from user-provided PowerPoint templates. |
| `skill-creator` | — | — | Meta-skill: guide for creating new skills. The recursion entry-point if Emerald authors firm-specific skills. |

> **Most-bundled skills:** `audit-xls` (7 agents), `xlsx-author` (7 agents),
> `pptx-author` (3 agents). These are the workhorses — almost every agent
> that produces an artifact uses one or both.

---

## §2 · equity-research (9 skills) — coverage + publishing

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `earnings-analysis` | `/earnings` | earnings-reviewer | 8–12 page earnings update reports for covered names. Beat/miss, key metrics, updated estimates, revised thesis. 1–3 tables + 8–12 charts. |
| `earnings-preview` | `/earnings-preview` | earnings-reviewer | Pre-earnings analysis — estimate models, scenario frameworks, key metrics to watch. Bull/bear setup. |
| `model-update` | `/model-update` | earnings-reviewer | Update financial models with new data (quarterlies, guidance, macro, revised assumptions). |
| `morning-note` | `/morning-note` | earnings-reviewer | 7am morning-meeting notes — overnight developments, trade ideas, key events for coverage stocks. |
| `sector-overview` | `/sector` | market-researcher, pitch-agent | Industry/sector landscape reports — dynamics, positioning, players, themes. |
| `idea-generation` | `/screen` | market-researcher | Systematic stock screening + idea sourcing. Quant screens + thematic + pattern recognition. **Note: V(A) survivorship-bias review required (per EMERALD_ADAPTATION.md §2.2.1).** |
| `initiating-coverage` | `/initiate` | — | Institutional-quality initiation reports via 5-task workflow (research → modeling → valuation → charts → assembly). |
| `catalyst-calendar` | `/catalysts` | — | Calendar of upcoming catalysts across coverage — earnings, conferences, product launches, regulatory, macro. |
| `thesis-tracker` | `/thesis` | — | Maintain investment theses — track data points, catalysts, milestones over time. |

> **Highest Emerald value.** This is the most directly applicable vertical
> for Emerald Investment Advisors. `earnings-analysis`, `model-update`,
> `morning-note`, `thesis-tracker`, `catalyst-calendar` are all daily-rhythm
> deliverables for an equity research shop.

---

## §3 · investment-banking (9 skills) — deal materials

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `pitch-deck` | — | pitch-agent | Populate IB pitch-deck templates from source files (Excel/CSV). Not for creating decks from scratch. |
| `cim-builder` | `/cim` | — | Confidential Information Memorandum drafting for sell-side M&A. |
| `teaser` | `/teaser` | — | Anonymous one-page company teasers — pre-NDA buyer-interest gauge. |
| `buyer-list` | `/buyer-list` | — | Strategic + financial buyer universe for sell-side mandates. |
| `merger-model` | `/merger-model` | — | Accretion/dilution analysis — pro-forma EPS, synergy sensitivities, PPA. |
| `process-letter` | `/process-letter` | — | Process letters + bid instructions for sell-side processes. |
| `deal-tracker` | `/deal-tracker` | — | Multi-deal pipeline view — milestones, deadlines, action items, status. |
| `datapack-builder` | — | — | Build IC-ready Excel data packs from CIMs, OMs, SEC filings, web search, MCPs. |
| `strip-profile` | `/one-pager` | — | Investment banking strip profiles — 1–4 information-dense slides with quadrant layouts. |

> **Emerald applicability: low.** Emerald is RIA, not IB. None of these skills
> map directly to RIA workflow except `datapack-builder`, which has generic
> data-extraction utility.

---

## §4 · private-equity (10 skills) — sourcing through portfolio ops

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `deal-sourcing` | `/source` | — | Discover targets, check CRM, draft founder outreach. |
| `deal-screening` | `/screen-deal` | — | Quick pass/fail framework on inbound CIMs/teasers. One-page screening memo. |
| `dd-checklist` | `/dd-checklist` | — | Sector-tailored due-diligence checklists with status tracking, red-flag escalation. |
| `dd-meeting-prep` | `/dd-prep` | — | Prep for management presentations, expert-network calls, customer references. |
| `unit-economics` | `/unit-economics` | — | ARR cohorts, LTV/CAC, net retention, payback, revenue quality, margin waterfall. |
| `returns-analysis` | `/returns` | valuation-reviewer | IRR/MOIC sensitivity tables across entry multiple, leverage, exit, growth, hold. |
| `ic-memo` | `/ic-memo` | valuation-reviewer | Investment committee memo drafting — synthesizes diligence, financials, deal terms. |
| `portfolio-monitoring` | `/portfolio` | valuation-reviewer | Track portco performance vs. plan — KPI extraction, variances, dashboards, covenant checks. |
| `value-creation-plan` | `/value-creation` | — | 100-day post-close plans, EBITDA bridges, operating-partner materials. |
| `ai-readiness` | `/ai-readiness` | — | Scan portfolio for highest-leverage AI opportunities. **Meta-relevant for Emerald's own AI rollout planning.** |

> **Emerald applicability: medium-low.** Direct applicability only if Emerald
> Advisors operates a private-fund vehicle. `unit-economics` and
> `returns-analysis` have crossover utility for any equity research that
> covers SaaS / recurring-revenue names.

---

## §5 · wealth-management (6 skills) — advisor workflows

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `client-review` | `/client-review` | meeting-prep-agent | Pre-meeting prep — performance summary, allocation analysis, talking points, action items. |
| `client-report` | `/client-report` | meeting-prep-agent | Quarterly/annual client-facing performance reports — returns, allocation, market commentary. |
| `financial-plan` | `/financial-plan` | — | Comprehensive financial plans — retirement projections, education, estate, cash flow. |
| `investment-proposal` | `/proposal` | meeting-prep-agent | Prospect-facing investment proposals — approach, allocation, expected outcomes, fees. |
| `portfolio-rebalance` | `/rebalance` | — | Allocation drift analysis + rebalancing trade recommendations. Tax + transaction costs + wash-sale aware. |
| `tax-loss-harvesting` | `/tlh` | — | TLH opportunity identification — unrealized losses, replacement securities, wash-sale tracking. |

> **Emerald applicability: depends on the Advisors arm's mandate type.**
> Reg S-P 2024 acute on `client-review`, `client-report`, `investment-proposal`
> (all NPI-handling). `portfolio-rebalance` and `tax-loss-harvesting` are
> high-value for any tax-aware SMA workflow.

---

## §6 · fund-admin (6 skills) — GL recon + close

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `gl-recon` | — | gl-reconciler | Reconcile GL ↔ subledger for trade date or period — match positions/transactions, surface breaks, classify by likely cause. |
| `break-trace` | — | gl-reconciler | Root-cause a recon break to source transaction. Audit-trail follow. |
| `accrual-schedule` | — | month-end-closer | Period-end accrual schedule — for each accrual, compute entry, cite support, draft JE (draft only, not posting). |
| `roll-forward` | — | month-end-closer | Roll-forward schedule for a balance-sheet account — beginning + activity − reversals = ending, tied to GL. |
| `variance-commentary` | — | month-end-closer | Flux commentary for every P&L and BS line over threshold — current vs prior + vs budget, driver-explained. |
| `nav-tieout` | — | statement-auditor | Tie an LP statement to fund NAV pack — recompute the LP's capital account, flag mismatches. |

> **Emerald applicability: low unless Emerald runs in-house fund admin.**
> Most small RIAs use third-party fund administrators.

---

## §7 · operations (2 skills) — KYC

| Skill | Slash command | Bundled by | Description |
|---|---|---|---|
| `kyc-doc-parse` | — | kyc-screener | Parse onboarding packet into structured KYC fields — identity, ownership, control, source of funds, document inventory. |
| `kyc-rules` | — | kyc-screener | Apply firm KYC/AML rules grid — risk rating, rule outcomes (cited), gaps + escalations. **Decides nothing; scores and routes only.** |

> **Emerald applicability: required if RIA AML rule (effective 2026) applies.**
> Rules-grid must be replaced with Emerald's actual written KYC policy
> (per EMERALD_ADAPTATION.md §2.7.2).

---

## §8 · lseg (partner, 8 skills) — fixed income, FX, options, macro

| Skill | Slash command | Description |
|---|---|---|
| `bond-relative-value` | `/analyze-bond-rv` | RV analysis — pricing, yield curves, credit spreads, scenario stress. |
| `bond-futures-basis` | `/analyze-bond-basis` | Futures basis analysis — pricing futures, CTD identification, implied repo, basis trades. |
| `swap-curve-strategy` | `/analyze-swap-curve` | Swap curve analysis — multi-tenor pricing, govt + inflation overlay, steepener/flattener/butterfly trades. |
| `fx-carry-trade` | `/analyze-fx-carry` | FX carry — spot, forwards, rate diffs, vol surfaces, historical trends, carry-to-vol. |
| `option-vol-analysis` | `/analyze-option-vol` | Vol-surface analysis — pricing, Greeks, implied-vs-realized, vol-trading strategies. |
| `macro-rates-monitor` | `/macro-rates` | Macro + rates dashboards — indicators, yield curves, breakevens, swap rates. |
| `equity-research` | `/research-equity` | LSEG-data equity research snapshots — consensus, fundamentals, prices, macro context. |
| `fixed-income-portfolio` | `/review-fi-portfolio` | FI portfolio review — multi-bond pricing, ref data, cashflows, scenario analysis. Duration + DV01 + waterfall. |

> **Requires LSEG subscription.** MCP at `https://api.analytics.lseg.com/lfa/mcp/server-cl`.
> Skills assume LSEG-vended data structure. Not directly usable without LSEG.

---

## §9 · spglobal (partner, 3 skills) — Capital IQ tearsheets + earnings + funding

| Skill | Slash command | Description |
|---|---|---|
| `tear-sheet` | — | Company tear sheets via Kensho LLM-ready API. 4 audience types (equity research, IB/M&A, corp dev, sales/BD). Public + private companies. |
| `earnings-preview-beta` | — | 4–5 page equity earnings preview — recent transcript, competitor landscape, valuation, news → HTML report. |
| `funding-digest` | — | One-page PowerPoint summarizing recent funding rounds + capital-markets activity across watched sectors/companies. |

> **Requires S&P Capital IQ + Kensho LLM-ready API.** MCP at
> `https://kfinance.kensho.com/integrations/mcp`. Skills are Apache-2.0
> licensed (upstream `kensho-technologies/spglobal-agent-skills`).

---

## Cross-cutting observations

1. **Skill triggers are documented in the description.** Each SKILL.md
   frontmatter description lists trigger phrases ("triggers on …",
   "use when …"). When Claude is operating with a skill loaded, those
   phrases activate the skill automatically. **For Emerald: when
   authoring firm skills, follow this convention so skill activation is
   predictable.**

2. **Skills are heavy.** A typical SKILL.md is hundreds of lines (DCF
   alone is 865+). They contain methodology, formula libraries, worked
   examples, output conventions. They are not lightweight prompts — they
   are reference manuals.

3. **Skill composition is the agent's superpower.** Look at `pitch-agent`'s
   skill list (11 skills) — the agent's value is *coordinating* skills
   sequentially: scope → sector-overview → comps-analysis → lbo-model →
   dcf-model → 3-statement-model → audit-xls → pitch-deck → ib-check-deck
   → deck-refresh. The orchestrator's system prompt is the recipe; skills
   are the ingredients.

4. **`xlsx-author` and `pptx-author` are infrastructure, not domain
   knowledge.** They exist because Managed Agents run headless (no live
   Office). For Cowork or Office add-in deployments, you'd write to a
   live workbook instead. Phase 2 OQ-7 noted the Office-JS branching at
   the top of dcf-model SKILL.md.

5. **`skill-creator` is the recursion door.** If Emerald wants to author
   firm-specific skills, this meta-skill is the documented entry point.
   See EXTENSION_PLAYBOOK.md for the workflow.

6. **Slash commands are vertical-scoped.** A command in `equity-research/commands/`
   is invoked as `/<plugin>:<command>` (e.g. `/equity-research:earnings`).
   Plugin name comes from the `<vertical>/.claude-plugin/plugin.json`.
