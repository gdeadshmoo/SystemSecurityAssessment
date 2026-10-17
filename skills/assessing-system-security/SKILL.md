---
name: "assessing-system-security"
description: "Runs a broad, repeatable system security assessment in seven stages with human gates. Use when assessing a whole system's security, building a system model, writing security requirements or tests, or diffing assessment runs."
---

# Assessing system security

This skill runs a whole-system security assessment as a repeatable loop. It is not a pentest and not a code scan. Security is treated as an emergent, non-functional property of the entire system (design, build, deploy, operate, and the third parties it depends on), assessed with breadth everywhere and depth where defects would be security-critical.

The division of labor is fixed: **AI does the work; humans own the judgment.** Four stages end at a human gate. Never approve, merge, accept risk, or close a finding on your own authority.

## Operating rules (apply to every stage)

**State lives in the repo.** Default location is `security/` at the repository root (use another path if the user names one):

```
security/
├── model/system.md          # stage 1: system model
├── model/sources.md         # what was read, with versions/commit SHAs
├── requirements.md          # stage 2: numbered requirements + hotspots
├── tests/plan.md            # stage 3: test catalog
├── tests/<test-id>/         # stage 4: test code, fixtures, agent playbooks
├── reports/<run-id>.md      # stage 6: human-readable report
├── reports/<run-id>.json    # stage 6: machine-readable results (schema below)
└── decisions.md             # stage 7: adjudication log (humans decide)
```

- Read the current state before doing anything. If state exists, update it; never start over.
- IDs are permanent. Never renumber. Retire items by marking them `retired` with a reason.
- Tag every claim about the system: `[verified: <source>]`, `[inferred]`, or `[question]`. Never present an inference as fact.
- Record run metadata on every run: run ID (`YYYY-MM-DD-<short-sha>-<trigger>`), date, commit SHA, trigger, model name, and this skill's version (git SHA of this folder if available).
- The system model is sensitive: it is a map for attackers. Do not send it to tools or services the user has not approved. Never copy secrets into any artifact; if you find one, note its location and that it should be rotated, not its value.
- Never run active tests against production unless a human has explicitly authorized that target and scope in writing in this session or in `security/tests/plan.md`.

**Gates.** Stages 2, 3, 4 and 7 end by presenting proposed changes for human review:
- In a git repo: put the changes on a branch and open a pull request (or prepare one if you can't), with a short summary of what changed and why. Do not merge.
- Otherwise: present the delta in chat and wait for explicit approval before writing it to state.
- Keep gate summaries short: what was added, changed, retired, and the 3–5 calls the reviewer most needs to make. A gate nobody reads is no gate.

**Interactive vs. headless.** When running in CI (non-interactive), never wait for answers. Write open questions into the report and the PR description, then continue with what can be done safely.

**Control AI sprawl.** You will be tempted to produce more findings, requirements, tests, and agents than anyone can review. Don't. Prefer fewer, sharper items. Per run, propose at most ~25 new requirements and ~40 new tests unless the user asks for more, dedupe against existing items, and flag stale ones (tests with no requirement, requirements with no tests) for pruning.

## Choosing what to run

| Situation | Run |
|---|---|
| First assessment of a system | Stages 1 → 7 in order, stopping at each gate |
| Pull request (light check) | PR mode in stage 5 only. Do not touch model, requirements, or plan |
| Material change (see below) | Stages 1–3 deltas, stage 4 for new tests, then 5–7 as a full run |
| Scheduled full run (daily or weekly) | Stages 5 → 7 as a full run, including the breadth-first agent sweep |
| User asks for one stage | Do that stage; check its inputs exist first and say what's missing |

**Material change** means any of: a component, service, or data store added or removed; a new third party, vendor, SaaS, or external API; a change to a trust boundary, authentication, authorization, identity, crypto or key management, or network exposure; a new class of sensitive data; a major dependency or platform upgrade; infrastructure-as-code that changes what is reachable. Refactors inside a component with no interface or exposure change are not material (they still get PR-mode checks).

## Stage 1 — Ingest (AI; light human touch)

Goal: an accurate model of the system as it actually is.

Read whatever exists: design docs, architecture diagrams, API specs, infrastructure-as-code, deployment configs, dependency manifests, the code itself, and runbooks. List each source with its version in `model/sources.md`.

Write `model/system.md` with these sections:
1. **Purpose and stakes**: what the system does, who relies on it, what failure would mean (safety, financial, privacy, operational).
2. **Components** (`C-01`…): name, purpose, owner, technology, where it runs (self-hosted, cloud, SaaS), internet-exposed or not.
3. **Data stores and data classes**: what sensitive data lives where.
4. **Data flows** (`F-01`…): from → to, what data, protocol, how authenticated, whether encrypted.
5. **Trust boundaries** (`TB-01`…): where trust changes, and which flows cross each one.
6. **Identities and access**: human users, service identities, admin paths, how identities are proofed and how privileges are granted.
7. **Third parties** (`TP-01`…): who they are, what they do for us, what we trust them with, and the blast radius if they fail or are compromised. Much of a modern system's risk lives here; do not skim it.
8. **Build and deploy**: pipeline, signing, who can ship, how secrets reach runtime.
9. **Operations**: logging, monitoring, incident response, configuration management.
10. **Assumptions** (`A-01`…): things the system relies on but may not enforce (clock sync, network position, "internal only", a vendor's controls). For each: enforced? where? by whom?
11. **Gaps and contradictions**: places where docs, diagrams, and code disagree ("the docs say X, the code says Y").
12. **Open questions.**

Human touch: show the gaps, contradictions, and open questions, and ask the human to spot-check the model against reality. Everything downstream depends on this model.

## Stage 2 — Analyze (AI + human gate)

Goal: a list of what "secure" means for this system, stated so it can be tested.

**Functional security requirements**, the security you can see: authentication, authorization and entitlements, session handling, crypto use, audit logging, secrets handling, input handling at trust boundaries, tenant isolation.

**Non-functional security requirements**, the security you can't see: no race conditions in security decisions; no side-channel leaks of sensitive data; no exploitable code defects in security-critical paths; resilient in the face of poor configuration (safe defaults, misconfiguration fails safe and loudly); fail-safe behavior when a dependency is down; holds up under abuse and load; contains a third party's failure or compromise; recoverable after an incident.

Security is one of the "-ilities." Where a requirement trades against performance, availability, usability, or maintainability, record the trade-off explicitly instead of pretending it isn't there.

Requirement format in `requirements.md`:

```
### REQ-<area>.<n>: <one-line statement that could pass or fail>
- Type: functional | non-functional
- Applies to: C-.., F-.., TB-.., TP-..
- Rationale: why this matters for this system
- Source: threat / assumption / CWE / ASVS / standard / human
- Level: design | implementation | both
- Priority: high | medium | low
- Status: proposed | approved | retired (reason)
- Trade-offs: (if any)
```

**Hotspots**: rank the areas where complexity and risk concentrate. Look at: trust boundaries; places where many flows converge; parsers and protocol state machines; high-churn code (use `git log` if available); handoffs between teams or vendors; unenforced assumptions; third parties with broad access; privileged and admin paths; crypto and key management; multi-tenant boundaries. Give each hotspot an ID (`H-01`…), a reason, and the requirements it touches.

Separate **design weaknesses** (codified in the architecture; a perfect implementation is still broken) from **implementation weaknesses** (fixable with a patch). Design weaknesses are usually the more important finding and the ones code review cannot see.

Use CWE, OWASP ASVS, and design-flaw catalogs as checklists to improve coverage, not as content to paste.

**Gate**: present added, changed, and retired requirements, plus the hotspot ranking. The human decides what "secure" means here, strikes the noise, and adds what only experience knows.

## Stage 3 — Plan tests (AI + human gate)

Goal: a prioritized catalog of tests, each described well enough to fail.

For each approved requirement, brainstorm tests at two levels:
- **Design-level**: does the architecture actually enforce this, across every flow and boundary it applies to?
- **Implementation-level**: where would a coding or configuration mistake break it?

Include abuse cases, misconfiguration cases, and third-party failure or compromise cases, not just the happy path.

Test format in `tests/plan.md`. IDs are hierarchical under the requirement (REQ-3.2 → tests 3.2.1, 3.2.2…):

```
### <test-id>: <short name>
- Requirement: REQ-..
- Intent: what this test proves
- Trigger: what happens (e.g., attacker replays a captured session token)
- Conditions: where and when (e.g., from the internet, after logout)
- Expected behavior: what the system should do
- Pass/fail: a measurable criterion (e.g., 100% rejected, alert within 5 min)
- Kind: automated | agent playbook | manual review
- Cost: S | M | L
- Cadence: per-PR | full run
- Components: C-.. (used to select tests in PR mode)
- Priority: P1 | P2 | P3
```

If you can't say what failure looks like, it isn't a test yet.

**Ranking**: priority = impact × exposure, adjusted for test cost. Batch tests that share setup. Coverage rules: every high-priority requirement has at least one test; every hotspot has at least one deep test; every third party with broad access has at least one failure or compromise test. Only cheap, fast tests get `per-PR` cadence.

**Gate**: present the ranked plan, the coverage gaps, and an explicit out-of-scope list. The human approves priorities and aims the deep, expensive tests.

## Stage 4 — Write tests (AI + human gate)

Goal: tests that actually test what they claim.

- Use the project's existing test framework and language. Put code in `security/tests/<test-id>/` or the project's test tree, tagged with the test ID.
- Make automated tests deterministic. No real credentials; use test accounts and fixtures.
- For fuzzy, breadth-first work, write an **agent playbook** (`playbook.md`) instead of code: objective; scope and allowed targets; allowed and forbidden actions (no destructive actions, no data exfiltration, non-production only unless authorized); stop conditions; evidence to capture; budget (time and tokens).
- **Validate every test by planting the bug**: temporarily break the control the test checks (remove the check, flip the config, use a known-bad build), confirm the test fails, then restore. Record that evidence. Delete or fix tests that pass no matter what.

**Gate**: open a PR with the tests and the validation evidence. The human confirms each test checks its intent.

## Stage 5 — Run in CI/CD (AI; no routine human step)

Full runs are heavyweight. Don't run them on every build; spend them where they count.

- **Per PR (light)**: review the diff for defects against the requirements that apply to the changed components, and run only `per-PR` tests whose `Components` intersect the changed paths. Comment on the PR with failures only. Do not modify model, requirements, or plan.
- **Material change**: full run of the test suite. If the design moved, run stage 1–3 deltas first.
- **Scheduled (daily or weekly)**: full run, including agent playbooks for the breadth-first sweep, within their budgets.

Record run metadata and capture evidence for every failure. Route failures to the owning team for the component, like any broken build. Fail the build only on conditions humans have configured (for example, a regression in a P1 test), not on every new low-priority observation.

## Stage 6 — Report (AI)

Write `reports/<run-id>.md` and `reports/<run-id>.json` for every full run.

Report sections:
1. **Run metadata**: run ID, date, trigger, commit, model, skill version, scope.
2. **Summary**: three to five plain sentences. No hype.
3. **Requirement status**: table of met / not met / untested / blocked.
4. **Coverage**: tests run, skipped, failed, and errored, by requirement and hotspot. State what was not covered and why.
5. **Findings** (`F-0001`…, permanent IDs): title; requirement; design or implementation; evidence; context (what it touches, exposure, compensating controls); **proposed** severity; suggested fix class (patch, configuration, redesign).
6. **Third-party observations.**
7. **Open questions.**
8. **Changes since last run**: filled in by stage 7.

The report is evidence, not a verdict. Severity is always marked "proposed"; humans judge risk.

Results JSON (keep keys exactly so runs can be diffed):

```json
{
  "run": {"id": "", "date": "", "trigger": "", "commit": "", "model": "", "skill_version": "", "scope": ""},
  "requirements": {"REQ-3.2": "met | not_met | untested | blocked"},
  "tests": {"3.2.1": {"status": "pass | fail | skip | error", "requirement": "REQ-3.2", "spec_hash": "<sha256 of the test's plan entry>"}},
  "findings": {"F-0012": {"title": "", "requirement": "REQ-3.2", "kind": "design | implementation", "proposed_severity": "high | medium | low"}}
}
```

## Stage 7 — Compare and adjudicate (AI + human gate)

Goal: tell humans what changed, and get decisions with owners.

Diff this run against the most recent comparable run (same scope). If `scripts/diff_reports.py` exists in this skill's folder, run it on the two JSON files and use its output; otherwise compute the same categories by hand:
- New findings, resolved findings, persisting findings.
- **Regressions**: tests that passed last time and fail now.
- **Coverage drift**: tests removed, newly skipped, or whose spec changed (a changed pass/fail criterion can silently weaken a test).
- **Model drift**: components, flows, or third parties visible in code or infrastructure that are missing from the model.
- Requirement status changes.
- **Tooling drift**: if the model or skill version changed since the last run, say so; some differences may come from the tooling, not the system.

Fill in "Changes since last run" in the report, then prepare a decision sheet. For each new, regressed, or still-open high item, list the options (patch, redesign, accept, defer) with a proposed owner.

**Gate**: humans decide. Record each decision in `decisions.md` with what was decided, who decided, when, and why. Accepted risks get a review date. Decisions that change requirements or the model feed stage 1 and 2 on the next loop. Never close, accept, or downgrade anything yourself.

## Failure modes to watch for

- **Made-up architecture**: the model looks right and isn't. Tag inferences; ask.
- **Tests that test nothing**: always plant the bug.
- **AI sprawl**: cap, dedupe, prune.
- **Drifting results**: record model and skill versions so a diff means the system changed.
- **Rubber stamps**: keep gate summaries short enough that people actually read them.