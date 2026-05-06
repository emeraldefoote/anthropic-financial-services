"""
test_scaffolding.py — Phase 4 machine-verifiable validation suite.

Run from anywhere via:
    pytest emerald-research/docs/tests/test_scaffolding.py -v

Verifies the integrity of the Emerald knowledge-scaffolding generated in
Phase 1–3 against SOURCE_REPO at the Phase-1-captured SHA. No auto-fix on
failure — failures are reported and the suite exits non-zero so the operator
can act.

Invariants (every test maps to one or more):

  I1.  Path-lockdown — no generated artifact resides outside SCAFFOLDING_ROOT
       (`emerald-research/`).
  I2.  Source-immutability — no SOURCE_REPO tracked file (anything outside
       `emerald-research/`) has been modified since the Phase-1 SHA.
  I3.  Injection-log invariant — `INJECTION_LOG.md` exists and is well-formed
       (header present); body may legitimately be empty.
  I4.  Required-artifact set — every Phase-3-required file exists.
  I5.  Path-citation existence — every `path[:N[-M]]` citation in any
       scaffolding artifact resolves to a real file (CWD-relative OR
       relative to the citing document's parent dir).
  I6.  Line-range integrity — every cited line range [N..M] is within the
       target file's actual line count.
  I7.  Prompt verbatim equality — every `untrusted-source` block in
       PROMPTS_CATALOG.md matches the cited file's content at the cited
       lines (with YAML literal-block-scalar de-indentation handled).
  I8.  Markdown link integrity — no dead internal markdown links in any
       scaffolding artifact.
  I9.  Per-agent coverage — every agent enumerated in RECON.md has a
       corresponding entry in ARCHITECTURE.md, EMERALD_ADAPTATION.md, and
       a per-agent CLAUDE.md mirror.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


# ─── Path discovery (relative to this test file) ────────────────────────────

TESTS_DIR = Path(__file__).resolve().parent
SCAFFOLDING_ROOT = TESTS_DIR.parent.parent          # emerald-research/
SOURCE_REPO = SCAFFOLDING_ROOT.parent                # the cloned repo

# Phase-1-captured invariants (do not change without operator review).
PHASE1_SHA = "bb4a2b3e53cf27f8900b33ed6a2d95ed32e57f1d"

NAMED_AGENTS = (
    "pitch-agent", "market-researcher", "earnings-reviewer",
    "meeting-prep-agent", "model-builder", "gl-reconciler",
    "kyc-screener", "valuation-reviewer", "month-end-closer",
    "statement-auditor",
)

REQUIRED_ARTIFACTS = (
    "CLAUDE.md",
    "docs/INJECTION_LOG.md",
    "docs/RECON.md",
    "docs/ARCHITECTURE.md",
    "docs/EMERALD_ADAPTATION.md",
    "docs/PROMPTS_CATALOG.md",
)

# Forward refs / proposed Emerald implementations that legitimately do not
# exist yet. They appear in scaffolding prose and must be excluded from
# path-existence checks.
ALLOWED_MISSING = frozenset({
    "docs/tests/test_scaffolding.py",   # this file (cited from CLAUDE.md root)
    "emerald/orchestrate_204_2.py",     # Emerald-side proposal in EMERALD_ADAPTATION.md
    # EXTENSION_PLAYBOOK.md proposes a hypothetical `coverage-monitor` agent
    # as a worked example for authoring new Emerald agents. These paths
    # don't exist yet by design — they describe what the operator would
    # create if they pursued that agent.
    "plugins/agent-plugins/coverage-monitor/agents/coverage-monitor.md",
    "managed-agent-cookbooks/coverage-monitor/agent.yaml",
    "subagents/news-scanner.yaml",
    "subagents/thesis-checker.yaml",
    "subagents/flag-writer.yaml",
    # Cookbook-relative bare paths in EXTENSION_PLAYBOOK that illustrate
    # the SKILL.md template via partial paths (the playbook says "see
    # dcf-model/SKILL.md as the canonical example" not as a citation).
    "dcf-model/SKILL.md",
    "kyc-rules/SKILL.md",
})

# Citation regexes
PATTERN_BACKTICK = re.compile(
    r'`([A-Za-z0-9._/\-]+\.(?:md|yaml|yml|json|py|sh|txt|mjs))'
    r'(?::(\d+)(?:[-,](\d+))?)?'
    r'`'
)
# Fence-header form inside `untrusted-source` blocks: `path:N-M:` on its own line
PATTERN_FENCE_HEADER = re.compile(
    r'^([A-Za-z0-9._/\-]+\.(?:md|yaml|yml|json|py|sh|txt|mjs))'
    r':(\d+)(?:[-,](\d+))?:\s*$',
    re.MULTILINE,
)
# Markdown link: [text](path-or-url)
PATTERN_MD_LINK = re.compile(r'\[[^\]]+\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


def _is_elision(p: str) -> bool:
    """`.../foo.md` and `foo/.../bar.md` are deliberate prose-elision
    placeholders, not real path citations. Skip them."""
    return "/..." in p or p.startswith("...")


def _resolve(citing_path: Path, target_str: str) -> Path | None:
    """Resolve a path string the way a careful reader would: try CWD-relative
    (i.e. relative to SOURCE_REPO root) first, then citing-doc-relative."""
    cwd_resolved = SOURCE_REPO / target_str
    if cwd_resolved.exists():
        return cwd_resolved
    doc_relative = citing_path.parent / target_str
    if doc_relative.exists():
        return doc_relative
    return None


def _scaffolding_md_files() -> list[Path]:
    """Every markdown file under SCAFFOLDING_ROOT (the body of the
    scaffolding's prose). Excludes the test file itself."""
    return sorted(SCAFFOLDING_ROOT.rglob("*.md"))


# ─── I1 + I2 — path-lockdown + source-immutability ──────────────────────────

def test_I1_path_lockdown_no_files_outside_scaffolding():
    """No generated file resides outside SCAFFOLDING_ROOT.

    Implementation: `git status --porcelain` shows the working tree's
    untracked + modified files. Anything not under `emerald-research/` is a
    write-lockdown breach.
    """
    out = subprocess.run(
        ["git", "-C", str(SOURCE_REPO), "status", "--porcelain"],
        check=True, capture_output=True, text=True,
    ).stdout

    # Each line is "<2-char status> <path>"; we only care about the path.
    breaches = []
    for line in out.splitlines():
        if not line.strip():
            continue
        path = line[3:].strip()
        # Handle "old -> new" rename form
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith("emerald-research/"):
            breaches.append(line)

    assert not breaches, (
        f"Path-lockdown breach — {len(breaches)} entries outside "
        f"emerald-research/:\n  " + "\n  ".join(breaches)
    )


def test_I2_source_repo_immutable_since_phase1():
    """No SOURCE_REPO tracked file (anything outside emerald-research/)
    has been modified since the Phase-1 SHA.

    Implementation: diff Phase-1 SHA against working tree, restricted to
    paths NOT under emerald-research/.
    """
    diff = subprocess.run(
        ["git", "-C", str(SOURCE_REPO), "diff", PHASE1_SHA, "--name-only"],
        check=True, capture_output=True, text=True,
    ).stdout

    modified_outside = [
        p for p in diff.splitlines()
        if p.strip() and not p.startswith("emerald-research/")
    ]

    assert not modified_outside, (
        f"Source-immutability breach — {len(modified_outside)} SOURCE_REPO "
        f"files modified since SHA {PHASE1_SHA[:8]}...:\n  "
        + "\n  ".join(modified_outside)
    )


# ─── I3 — injection-log invariant ───────────────────────────────────────────

def test_I3_injection_log_exists_and_wellformed():
    """INJECTION_LOG.md exists and has its header. Empty body (no entries) is
    a valid outcome; any entries must match the documented schema."""
    log = SCAFFOLDING_ROOT / "docs" / "INJECTION_LOG.md"
    assert log.exists(), f"INJECTION_LOG.md missing at {log}"

    text = log.read_text()
    assert "INJECTION_LOG.md" in text and "Untrusted-content surveillance" in text, (
        "INJECTION_LOG.md header missing or malformed"
    )

    # Find entries: lines matching `### [N] <tag>` in the Entries section,
    # excluding the schema-example heading inside the docstring.
    entries_section = text.split("## Entries", 1)
    if len(entries_section) < 2:
        pytest.fail("INJECTION_LOG.md missing '## Entries' section header")

    body = entries_section[1]
    entry_starts = re.findall(r'^### \[(\d+)\]', body, re.MULTILINE)

    # Each entry must declare the schema fields. We don't validate every
    # field exhaustively — just that they exist when there are entries.
    if entry_starts:
        for n in entry_starts:
            entry_block = re.search(
                rf'^### \[{n}\].*?(?=^### \[|\Z)', body, re.MULTILINE | re.DOTALL,
            )
            assert entry_block, f"Entry [{n}] block not parseable"
            for field in ("Trigger:", "Path", "Line range:", "Action taken:"):
                assert field in entry_block.group(), (
                    f"Entry [{n}] missing required field '{field}'"
                )


# ─── I4 — required-artifact set ─────────────────────────────────────────────

@pytest.mark.parametrize("rel", REQUIRED_ARTIFACTS)
def test_I4_required_top_level_artifacts_exist(rel):
    p = SCAFFOLDING_ROOT / rel
    assert p.exists(), f"Required artifact missing: {rel}"


@pytest.mark.parametrize("slug", NAMED_AGENTS)
def test_I4_per_agent_claude_mirror_exists(slug):
    p = SCAFFOLDING_ROOT / "agents" / slug / "CLAUDE.md"
    assert p.exists(), f"Per-agent mirror missing: agents/{slug}/CLAUDE.md"


# ─── I5 + I6 — citation existence + line-range integrity ────────────────────

def _collect_citations() -> list[tuple[Path, str, str | None, str | None]]:
    """Return every (citing_path, path_str, start, end) tuple found in any
    scaffolding markdown file via either citation pattern.

    Bare-filename citations (no `/`) are excluded — they would be ambiguous
    when many files share the same basename (e.g. `reader.yaml`, `note-writer.yaml`).
    Such bare-filename references are read in local prose-context and
    deliberately not machine-checked.
    """
    citations: list[tuple[Path, str, str | None, str | None]] = []
    for md in _scaffolding_md_files():
        text = md.read_text()
        for pat in (PATTERN_BACKTICK, PATTERN_FENCE_HEADER):
            for m in pat.finditer(text):
                p_str = m.group(1)
                if "/" not in p_str:        # ambiguous bare filename — skip
                    continue
                citations.append((md, p_str, m.group(2), m.group(3)))
    return citations


def test_I5_every_qualified_path_citation_resolves():
    citations = _collect_citations()
    failures = []
    skipped_elision = 0
    skipped_allowed = 0

    for citing, p_str, _, _ in citations:
        if _is_elision(p_str):
            skipped_elision += 1
            continue
        if p_str in ALLOWED_MISSING:
            skipped_allowed += 1
            continue
        if _resolve(citing, p_str) is None:
            failures.append(f"{citing.relative_to(SOURCE_REPO)} -> `{p_str}`")

    # Diagnostics — printed even on pass via `-v -s`
    print(
        f"\n  citations checked: {len(citations)}; "
        f"elided: {skipped_elision}; allowed forward refs: {skipped_allowed}; "
        f"failures: {len(failures)}"
    )

    assert not failures, (
        f"{len(failures)} qualified-path citation(s) do not resolve:\n  "
        + "\n  ".join(failures[:30])
    )


def test_I6_every_line_range_within_file_bounds():
    citations = _collect_citations()
    failures = []
    line_range_count = 0

    for citing, p_str, start, end in citations:
        if start is None or _is_elision(p_str) or p_str in ALLOWED_MISSING:
            continue
        target = _resolve(citing, p_str)
        if target is None:
            continue                        # I5 reports missing files
        line_range_count += 1
        n = sum(1 for _ in target.open())
        s = int(start)
        e = int(end) if end else s
        if not (1 <= s <= n and 1 <= e <= n and s <= e):
            failures.append(
                f"{citing.relative_to(SOURCE_REPO)} -> `{p_str}:{start}"
                f"{'-'+end if end else ''}` (target has {n} lines)"
            )

    print(f"\n  line-ranges checked: {line_range_count}; failures: {len(failures)}")

    assert not failures, (
        f"{len(failures)} line range(s) out of file bounds:\n  "
        + "\n  ".join(failures[:30])
    )


# ─── I7 — prompts catalog string-equality regression ────────────────────────

PROMPTS_CATALOG = SCAFFOLDING_ROOT / "docs" / "PROMPTS_CATALOG.md"

# Match an entire ```untrusted-source\n<path>:<lines>:\n<body>\n``` block.
PATTERN_UNTRUSTED_BLOCK = re.compile(
    r'```untrusted-source\n'
    r'([^\n]+\.(?:md|yaml|yml|py)):(\d+)(?:[-,](\d+))?:\n'
    r'(.*?)\n'
    r'```',
    re.DOTALL,
)


def _yaml_literal_block_dedent(lines: list[str]) -> list[str]:
    """If every non-empty line begins with the same leading whitespace
    (the YAML literal-block-scalar indent), strip it. Otherwise return
    lines unchanged."""
    nonempty = [ln for ln in lines if ln.strip()]
    if not nonempty:
        return lines
    indents = [len(ln) - len(ln.lstrip(" ")) for ln in nonempty]
    common = min(indents)
    if common == 0:
        return lines
    return [ln[common:] if len(ln) >= common else ln for ln in lines]


def test_I7_prompts_catalog_string_equality():
    assert PROMPTS_CATALOG.exists(), "PROMPTS_CATALOG.md missing"
    catalog = PROMPTS_CATALOG.read_text()

    blocks = list(PATTERN_UNTRUSTED_BLOCK.finditer(catalog))
    assert blocks, "No untrusted-source blocks found in PROMPTS_CATALOG.md"

    failures = []
    for m in blocks:
        path_str = m.group(1)
        s = int(m.group(2))
        e = int(m.group(3)) if m.group(3) else s
        quoted = m.group(4)

        target = _resolve(PROMPTS_CATALOG, path_str)
        if target is None:
            failures.append((path_str, s, e, "file not found"))
            continue

        lines = target.read_text().splitlines()
        if e > len(lines):
            failures.append((path_str, s, e, f"line range OOR (file={len(lines)})"))
            continue

        actual_lines = lines[s - 1:e]
        actual = "\n".join(actual_lines)
        actual_dedented = "\n".join(_yaml_literal_block_dedent(actual_lines))

        if actual.rstrip() == quoted.rstrip():
            continue                        # exact match (orchestrator prompts, code blocks)
        if actual_dedented.rstrip() == quoted.rstrip():
            continue                        # YAML literal-block dedent match (subagent prompts)
        failures.append((path_str, s, e, "content mismatch"))

    print(f"\n  untrusted-source blocks: {len(blocks)}; failures: {len(failures)}")

    assert not failures, (
        f"{len(failures)} verbatim-extraction mismatch(es):\n  "
        + "\n  ".join(f"{p}:{s}-{e} -- {why}" for (p, s, e, why) in failures[:30])
    )


# ─── I8 — markdown link integrity ───────────────────────────────────────────

def test_I8_no_dead_internal_markdown_links():
    failures = []
    link_count = 0

    for md in _scaffolding_md_files():
        text = md.read_text()
        for m in PATTERN_MD_LINK.finditer(text):
            href = m.group(1)
            link_count += 1

            # External and anchor-only links are out of scope.
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            # Strip fragment
            target_str = href.split("#", 1)[0]
            if not target_str:
                continue
            if _is_elision(target_str) or target_str in ALLOWED_MISSING:
                continue

            target = _resolve(md, target_str)
            if target is None:
                failures.append(f"{md.relative_to(SOURCE_REPO)} -> [{href}]")

    print(f"\n  internal links checked: {link_count}; failures: {len(failures)}")

    assert not failures, (
        f"{len(failures)} dead internal markdown link(s):\n  "
        + "\n  ".join(failures[:30])
    )


# ─── I9 — per-agent coverage ────────────────────────────────────────────────

@pytest.mark.parametrize("slug", NAMED_AGENTS)
def test_I9_agent_in_recon_md(slug):
    text = (SCAFFOLDING_ROOT / "docs" / "RECON.md").read_text()
    assert slug in text, f"agent slug `{slug}` absent from RECON.md"


@pytest.mark.parametrize("slug", NAMED_AGENTS)
def test_I9_agent_in_architecture_md(slug):
    text = (SCAFFOLDING_ROOT / "docs" / "ARCHITECTURE.md").read_text()
    assert slug in text, f"agent slug `{slug}` absent from ARCHITECTURE.md"


@pytest.mark.parametrize("slug", NAMED_AGENTS)
def test_I9_agent_in_emerald_adaptation_md(slug):
    text = (SCAFFOLDING_ROOT / "docs" / "EMERALD_ADAPTATION.md").read_text()
    assert slug in text, f"agent slug `{slug}` absent from EMERALD_ADAPTATION.md"


@pytest.mark.parametrize("slug", NAMED_AGENTS)
def test_I9_agent_in_prompts_catalog_md(slug):
    """Every named agent must have its orchestrator system prompt extracted
    in PROMPTS_CATALOG.md as an `untrusted-source` block."""
    text = PROMPTS_CATALOG.read_text()
    assert f"plugins/agent-plugins/{slug}/agents/{slug}.md:1-" in text, (
        f"orchestrator system prompt for `{slug}` missing from PROMPTS_CATALOG.md"
    )


# ─── Summary printer (runs after all tests via the conftest hook below) ─────

def test_zz_summary_print():
    """Last test alphabetically — prints a summary of what was checked.
    Always passes; exists to surface the corpus stats in the test log.
    """
    md_files = _scaffolding_md_files()
    citations = _collect_citations()
    print(f"\n=== Phase 4 verification corpus ===")
    print(f"  Phase-1 SHA:                      {PHASE1_SHA}")
    print(f"  SCAFFOLDING_ROOT:                 {SCAFFOLDING_ROOT}")
    print(f"  SOURCE_REPO:                      {SOURCE_REPO}")
    print(f"  scaffolding markdown files:       {len(md_files)}")
    print(f"  total qualified path citations:   {len(citations)}")
    print(f"  named agents covered (I9):        {len(NAMED_AGENTS)}")
    print(f"  required artifacts (I4):          "
          f"{len(REQUIRED_ARTIFACTS)} top-level + {len(NAMED_AGENTS)} per-agent")
    assert True
