# How to run an AI-enabled system security assessment

This guide shows how to use the `assessing-system-security` skill
([`skills/assessing-system-security/SKILL.md`](skills/assessing-system-security/SKILL.md))
to assess a whole system the way you build it: AI does the work, and humans own the judgment.
The talk behind it is in [`presentation/`](presentation/).

The short version: **write down the system, turn it into testable requirements, turn those into
tests that can fail, run them on a schedule, and diff each run against the last.** A person signs
off at four gates.

---

## 1. What this is, and what it isn't

- **It isn't a pentest.** A pentest finds vulnerabilities at one point in time. It doesn't tell you
  how secure the system is, and it's out of date by the next deploy.
- **It isn't only AI code review.** Code review on every PR is necessary, but it can't see design
  flaws, how components behave together, deployment and operations, or whether the requirements
  are right in the first place.
- **It is** a repeatable, whole-system assessment. It treats security as an *emergent,
  non-functional property* of design, build, deploy, operations, and third parties. It goes broad
  everywhere and deep where a defect would be security-critical.

Why now: AI-driven attackers work breadth-first. They try every mistake and misconfiguration,
everywhere, continuously. AI-assisted development also ships code faster than ever. An annual,
depth-first assessment can't keep up with either.

---

## 2. Install the skill

The skill is one file, `SKILL.md`, in a folder named `assessing-system-security`.

**Claude Code (per repository, shared with your team):**

```bash
mkdir -p .claude/skills
cp -r skills/assessing-system-security .claude/skills/
git add .claude/skills/assessing-system-security && git commit -m "Add security assessment skill"
```

**Claude Code (just for you, every project):** copy the folder to `~/.claude/skills/`.

**Claude apps (claude.ai / desktop):** zip the `assessing-system-security` folder and upload it in
the Skills section of Settings. If you're on a Team or Enterprise plan, an admin can share it
across the organization.

To check it loaded, ask Claude *"What skills do you have for security assessment?"*, or just start
with a request like the ones in section 4. The skill triggers on requests about assessing a whole
system, building a system model, writing security requirements or tests, or diffing assessment
runs.

---

## 3. How it works: seven stages, four human gates

| # | Stage | Who | Output (under `security/` in the repo) |
|---|---|---|---|
| 1 | **Ingest** | AI, with a light human touch | `model/system.md`, `model/sources.md` |
| 2 | **Analyze** | AI + **human gate** | `requirements.md` (numbered REQs + hotspot map) |
| 3 | **Plan tests** | AI + **human gate** | `tests/plan.md` (ranked, hierarchical test IDs) |
| 4 | **Write tests** | AI + **human gate** | `tests/<test-id>/` (code, fixtures, agent playbooks) |
| 5 | **Run in CI/CD** | AI | test results |
| 6 | **Report** | AI | `reports/<run-id>.md` and `.json` |
| 7 | **Compare & adjudicate** | AI + **human gate** | diff vs. last run, `decisions.md` |

Ground rules the skill follows on every run:

- **State lives in the repo**, versioned next to the code. Each run updates the existing state and
  never starts from scratch. IDs (C-, F-, TB-, TP-, A-, REQ-, H-, test IDs, finding IDs) are
  permanent. Retired items stay in the files, marked `retired` with a reason.
- **Every claim is tagged** `[verified: <source>]`, `[inferred]`, or `[question]`.
- **Gates are pull requests.** At stages 2, 3, 4 and 7 the skill opens a PR (or, outside git,
  shows the changes in chat) and waits for you. It never merges, accepts risk, or closes a
  finding by itself.
- **Sprawl is capped**: about 25 new requirements and 40 new tests per run, deduplicated, with
  stale items flagged for pruning.
- **Safety**: the system model counts as sensitive (it's a map for attackers), secrets are never
  copied (only their location, plus a note to rotate them), and nothing runs against production
  without written authorization.

---

## 4. Your first assessment, step by step

Work in the repository for the system you're assessing, or one that holds its design docs and
infrastructure-as-code. Run the stages in order and stop at each gate.

### Stage 1: Ingest

Give Claude the *real* description of the system, not the marketing version: design docs,
diagrams, API specs, infrastructure-as-code, deploy configs, dependency manifests, runbooks,
and the code.

> Use the assessing-system-security skill. Run stage 1 on this repo. Also read `docs/architecture/`
> and the Terraform in `infra/`.

**Your job:** read the *Gaps and contradictions* and *Open questions* sections, answer what you
can, and spot-check the components, flows, trust boundaries and third parties against reality.
Everything after this depends on the model being right.

### Stage 2: Analyze (gate)

> Run stage 2.

Claude drafts **functional** requirements (authentication, authorization, sessions, crypto, audit,
secrets, input handling, tenant isolation) and **non-functional** ones (no races in security
decisions, no side-channel leaks, safe behavior under misconfiguration, fail-safe when a
dependency is down, holds up under abuse, contains third-party compromise, recoverable). It also
ranks **hotspots** and separates design weaknesses from implementation weaknesses.

**Your job at the gate:** decide what "secure" means for *this* system. Remove the noise, add what
only experience tells you, record trade-offs (security against performance, availability,
usability, maintainability), and approve the hotspot map. Merge the PR when you agree with it.

### Stage 3: Plan tests (gate)

> Run stage 3 for the approved requirements.

Each test is written so it **can fail**, the same way you'd write a performance test:

| Element | Example |
|---|---|
| Trigger | Attacker replays a captured session token |
| Conditions | From the internet, after the user logs out |
| Expected behavior | Token rejected, event logged |
| Pass/fail | 100% rejected, alert within 5 min |

**Your job at the gate:** approve priorities, point the deep (expensive) tests at the critical
spots, and say out loud what is out of scope.

### Stage 4: Write tests (gate)

> Run stage 4 for the P1 tests.

Claude writes deterministic test code in your existing framework, plus **agent playbooks** for
fuzzy, breadth-first work. A playbook has an objective, scope, allowed and forbidden actions, stop
conditions, the evidence to capture, and a budget.

**Your job at the gate:** **plant the bug.** Break the control on purpose (remove the check, flip
the config), confirm the test goes red, then restore it. The skill records this evidence for you.
Delete any test that passes no matter what.

### Stage 5: Run in CI/CD

Pick a cadence:

| When | What runs |
|---|---|
| Every PR | Light check: diff review against the requirements for the changed components, plus `per-PR` tests whose components were touched. Model, requirements and plan aren't changed. |
| Material change (new component, vendor, trust boundary, auth/crypto change, new sensitive data, major upgrade, IaC that changes exposure) | Deltas for stages 1–3, new tests from stage 4, then a full run |
| Daily or weekly | Full run, including the agent-playbook sweep |

Full runs are heavy, so don't run them on every build. Route failures to the team that owns the
component, the same way you would a broken build. Fail the build only on conditions people
configured, such as a regression in a P1 test.

A headless run in CI looks roughly like this (adapt it to your pipeline):

```bash
claude -p "Use the assessing-system-security skill. Scheduled full run: stages 5 through 7. \
Trigger=weekly. Write open questions into the report; do not wait for answers."
```

You can also use the Claude Code GitHub Action with the same prompt, either on a schedule or on
pull requests (PR mode).

### Stage 6: Report

Every full run writes `security/reports/<run-id>.md` and a matching `.json` with fixed keys, so
runs can be diffed. Each report covers requirement status (met / not met / untested / blocked),
coverage test by test (including what *didn't* run), findings in context, design flaws and code
bugs called out separately, and severity marked as *proposed*. **The report is evidence, not a
verdict.**

### Stage 7: Compare & adjudicate (gate)

> Run stage 7 against the last full run.

Claude diffs the run against the previous one: new, resolved and persisting findings;
**regressions**; **coverage drift** (tests skipped, weakened or deleted); **model drift** (things in
the code or infrastructure that the model doesn't include); and **tooling drift** (a different
model or skill version). It then prepares a decision sheet.

**Your job at the gate:** judge the risk. For each item choose patch, redesign, accept or defer,
and name an owner. Decisions go in `decisions.md` with who decided, when and why. Accepted risks
get a review date. Anything that changes requirements or the model feeds the next loop.

---

## 5. A worked example (illustrative)

Following one requirement around the loop:

| Stage | What happens |
|---|---|
| 02 Analyze | **REQ-3.2**: session tokens are invalid after logout. A human approves it. |
| 03 Plan | **Test 3.2.1**: replay a captured token after logout. High priority. |
| 04 Write | AI writes a replay harness. A human plants the bug, and the test catches it. |
| 05 Run | Runs in every weekly full run and stays green for months. |
| 05 Run | A refactor of the session service counts as a material change. A full run triggers and 3.2.1 goes red. |
| 06–07 | The diff flags a regression against the last release. A human blocks the release and names an owner. |

---

## 6. When to start a new loop

- A design change
- A new component or vendor
- A new attack technique
- A finding in production
- The calendar (daily or weekly)

Each loop keeps the previous loop's tests, so coverage only grows.

---

## 7. Where this goes wrong (and why the gates exist)

| Failure mode | Guard |
|---|---|
| **Made-up architecture**: the model looks right and isn't | Inferences are tagged. A human spot-checks the model against reality. |
| **Tests that test nothing**: green forever | Plant the bug and prove the test fails. |
| **AI sprawl**: endless findings, tests and agents | Cap, deduplicate, prune. |
| **Drifting results** | Record the model and skill version on every run, so a diff means the *system* changed. |
| **A map for attackers** | Treat the system model as sensitive wherever it's processed. |
| **Rubber stamps** | Keep gate summaries short. A gate nobody reads isn't a gate. |

---

## 8. Start Monday

You don't need all seven stages on day one:

1. **Write down the system**, even on one page (stage 1).
2. **Have AI draft the requirements**, then argue with it (stage 2).
3. **Turn your top ten into numbered tests in CI** (stages 3–5).
4. **Diff each full run against the last**, then grow from there (stages 6–7).

---

## 9. Further reading

- McGraw, *Software Security: Building Security In* (2006)
- IEEE Center for Secure Design, *Avoiding the Top 10 Software Security Design Flaws* (2014)
- Shostack, *Threat Modeling: Designing for Security* (2014)
- *Threat Modeling Manifesto* (2020)
- NIST SP 800-160 Vol. 1, *Engineering Trustworthy Secure Systems*
- SEI ATAM quality attribute scenarios
- ISO/IEC 25010 (product quality model)
- OWASP ASVS
- MITRE CWE
