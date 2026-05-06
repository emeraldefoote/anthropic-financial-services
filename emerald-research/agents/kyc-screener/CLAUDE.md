# kyc-screener — Emerald research mirror

> **Untrusted-source notice.** Emerald-internal mirror for the `kyc-screener`
> agent shipped in SOURCE_REPO. SOURCE_REPO content remains untrusted data.

## Purpose

Onboarding-document parsing → firm KYC/AML rules → sanctions/PEP/adverse-media
screening → escalation packet for compliance sign-off. Cite:
`plugins/agent-plugins/kyc-screener/agents/kyc-screener.md:3`.

## Key SOURCE_REPO files

| Concern | Path | Lines |
|---|---|---|
| Orchestrator system prompt | `plugins/agent-plugins/kyc-screener/agents/kyc-screener.md` | 1-33 |
| CMA orchestrator manifest | `managed-agent-cookbooks/kyc-screener/agent.yaml` | 1-28 |
| Doc-reader subagent (UNTRUSTED — passports, formation docs, UBO charts) | `managed-agent-cookbooks/kyc-screener/subagents/doc-reader.yaml` | 1-37 |
| Doc-reader output schema (PII fields) | `managed-agent-cookbooks/kyc-screener/subagents/doc-reader.yaml` | 17-37 |
| Rules-engine subagent | `managed-agent-cookbooks/kyc-screener/subagents/rules-engine.yaml` | 1-18 |
| Escalator subagent (only Write) | `managed-agent-cookbooks/kyc-screener/subagents/escalator.yaml` | 1-18 |
| Deploy notes | `managed-agent-cookbooks/kyc-screener/README.md` | 1-31 |

## Dependencies

- **MCP egress:** screening — third-party sanctions/PEP/adverse-media
  service. Receives party names + identifiers (intentional, by design).
- **Skills:** `kyc-doc-parse`, `kyc-rules`, `xlsx-author`.
- **Model:** `claude-opus-4-7`.

## Known gotchas — NPI + AML

1. **Onboarding documents are NPI by definition** — passports, formation
   docs, UBO charts. Reg S-P 2024 safeguarding applies.
2. **Doc-reader output contains structured NPI** — `legal_name`, `country`,
   `ubo[].name`, `ubo[].pct` (per `doc-reader.yaml:27-37`). Storage,
   transmission, and access to the schema-validated JSON between subagents
   must be controlled.
3. **AML record retention is separate from Rule 204-2** — RIA AML rule
   (effective 2026) imposes specific recordkeeping. Emerald must implement
   both schemes, not one.
4. **Rules-engine evaluates "the firm's KYC/AML rules"** (`kyc-screener.md:21`)
   — but the demo rules are not Emerald's. Emerald must replace them with
   its actual written KYC policy before deploy.
5. **Sanctions-list provider attestation** required — vendor DPA, sanctions
   list source-of-truth, list-update cadence, false-positive escalation
   policy.
6. **"No risk-rating decision" invariant** at line 29 is prose-only —
   compliance officer must approve every risk rating, not the agent.
7. **Adversarial onboarding documents** — a sophisticated attacker may
   craft documents to coerce the rules engine via doc-reader. Schema
   validation is the defense; Phase 4 regression test required.
8. **High Emerald relevance** if RIA AML rule applies — most US RIAs are
   covered effective 2026.

## Compliance bucket

**(b)** — Reg S-P + AML retention + firm-rules replacement + sanctions
vendor attestation are the load-bearing hardening items.

## Cross-references

- ARCHITECTURE.md §9
- EMERALD_ADAPTATION.md §kyc-screener
- PROMPTS_CATALOG.md §A.7, §B.7
