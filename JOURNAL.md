## Week 7 — Issue selection

**Issue link:** https://github.com/ascherj/pathreview/issues/43

**Issue title:** Agent session state is not cleared between reviews for the same user #43

**Tier:** [X] Tier 1  [ ] Tier 2  [ ] Tier 3

**Problem summary:**
The issue stems from how `agent/orchestrator.py` interacts with the `SessionStore` in `agent/memory/session_store.py`. Specifically, the orchestrator's `run` method passes the user's `profile_id` as the cache key when storing and retrieving session state, rather than generating a unique identifier for each distinct review request. As a result, when a user requests a subsequent review, the orchestrator fetches stale tool results from their previous session instead of performing a new analysis. A successful fix will update the orchestrator to either clear the session state between requests or use a uniquely generated session ID, ensuring the agent always evaluates the user's most recent portfolio updates.

**Scope fit:**
I selected this issue because it aligns well with my current comfort level in Python, focusing on state management within a specific component rather than requiring sprawling architectural changes. Since I have 3-6 hours available for a Tier 1 issue, addressing the orchestrator's session logic is a realistic and appropriately scoped challenge.

**Branch name:** fix/43-agent-session-state-not-cleared

**Setup confirmation:** [X] App runs locally at localhost:5173

**Cohort ledger:** [X] Issue added to cohort ledger

---

## Week 8 — Reproduction & solution planning

**Reproduction commit link:** https://github.com/bbdevelops/pathreview/commit/c87b97f95f7421d3f614d1accbeac4cbf3ea5f16

**Reproduction summary:**
Ran `scripts/reproduce_issue_43.py`, which drives `Orchestrator.run()` twice for the same `profile_id` (README-only, then resume-only) against an in-memory fake Redis. After run 2, the persisted session state still contained `readme_scorer` from run 1 — confirming stale state leaks across reviews because `run()` merges new results onto prior state (`agent/orchestrator.py:66`) and re-keys on `profile_id`. Further code review found a second stale-data path: the in-memory `ContextManager` is instantiated once per Orchestrator (`:29`) rather than per review, so `cached_results` accumulates and `market_analyzer`'s constant input serves the prior run's result.

**PLAN.md link:** https://github.com/bbdevelops/pathreview/blob/fix/43-agent-session-state-not-cleared/PLAN.md

**Walkthrough video (recommended):** [link to your Loom video, ≤2 min — recommended, not graded]

**Blockers or open questions:**
The fix must clear **both** cache layers — the Redis `SessionStore` and the in-memory `ContextManager` (`orchestrator.py:29`/`:75`, with `market_analyzer` at `:130`); a Redis-only fix is partial. Also confirm whether wiring `Orchestrator` into the production review pipeline (`core/services/review_service.py::_run_agent_orchestration` is currently a placeholder) is in scope for #43 — assuming not; the fix is verified via the repro script and a new unit test.

---

### Part 1 — Understanding the Issue

**Can I explain what this issue is asking for in my own words?**

Paraphrase the issue without looking at it. If you can't, you don't understand it well enough yet. Read the full issue body, look at any linked PRs or comments, and try again.

[X] I can explain the problem and the expected behavior in 2–3 sentences without reading the issue.

**Do I understand which part of the app is affected?**

Check the labels on the issue — they often indicate the area (api, rag, ingestion, frontend, etc.). Look at the referenced files if any are mentioned. Find those files in the repo.

[X] I've located the relevant files and confirmed they exist in the codebase.

**Do I understand what "done" looks like?**

Can you describe what the app should do (or not do) once the issue is fixed? If the issue has acceptance criteria, read them carefully. If it doesn't, try writing your own — that forces you to understand the scope.

[X] I can describe a concrete before-and-after: what the user sees before the fix and what they see after.

---

### Part 2 — Tier Fit

**Is the tier a realistic match for where I am right now?**

[X] If this is my first open source contribution: I'm choosing Tier 1.

[ ] If I've contributed to large codebases before: Tier 2 or 3 is fair game.

[ ] I'm not choosing a Tier 3 issue to "challenge myself" if I haven't completed a Tier 1 or 2 first — scope surprises in Week 9 don't have a safety net.

---

### Part 3 — Codebase Readiness

**Can I find the relevant code?**

Before claiming the issue, locate the specific function, route, or module it describes. Don't rely on grep alone — open the file, read the surrounding context, and confirm you're in the right place.

[X] I've found and read the specific code the issue references (not just the file — the function or section).

**Do I understand the surrounding code well enough to change it safely?**

You don't need to understand the whole codebase. But you need to understand the file you're about to edit well enough to predict what a change will break. Read the function signatures, docstrings, and any callers.

[X] I've read enough surrounding context that I can write a rough plan for the fix without looking anything up.

**Have I read the relevant test file?**

Find the test file for the module your issue touches (tests/unit/ is the right place to start). Look at how existing tests are structured — fixtures, assertions, mock patterns. You'll need to write at least one new test.

[X] I've found the test file for my module and read at least one test end-to-end.

---

### Part 4 — Scope and Time

**How many others are already working on this issue?**

Claims are non-exclusive — more than one student may work on the same issue, and your grade comes from your own artifacts, never from being first. Still, check the issue comments and the Claims column in the Issue Catalog tab of the cohort ledger: a less-crowded issue of the same tier can mean smoother coaching and peer review.

[X] I've checked the issue comments and the ledger's Claims count, and I'm fine with how many others are on this issue.

**Is the scope realistic for Weeks 8–9?**

You have roughly two weeks to implement, test, and submit a PR. Tier 1 issues should take 3–6 hours of focused work. Tier 2 issues may take 8–12 hours. Tier 3 issues can take significantly longer.

Think about your week — other classes, work, other commitments. Is this achievable?

[X] I've estimated the time this will take and I'm confident I can complete it before the Week 9 deadline.

**Are there any blockers or dependencies?**

Some issues say "blocked by #X" or reference another issue that needs to be resolved first. Check the issue for any such dependencies.

[X] This issue has no open blockers or dependencies on other unresolved issues.
