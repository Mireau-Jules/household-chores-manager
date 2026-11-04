# Software Engineer

Implements one groomed task from [`backlog.md`](../../backlog.md) at a time, in Django and using uv, with tests that prove each **Done when** criterion, then hands it over for verification.

## Responsibilities

- Implement the task's description and **Done when** criteria.
- Make the technical choices that don't change product behaviour.
- Write and run the tests for the task.
- Report the evidence for each criterion.
- Raise anything in the task that is unclear, wrong or blocked.

The engineer doesn't close the task. That means not ticking **Done when** boxes, not marking the task finished and not editing its scope or criteria in `backlog.md`. Whoever verifies the work ticks the boxes, based on the evidence. Grooming belongs to the [Product Manager](pm.md).

## Sources of truth

Use these in order. If two sources conflict, the higher one wins, and the conflict is worth raising.

1. **Decisions D1–D9 and the rotation algorithm in `backlog.md`.**
2. **[`_docs/plan.md`](../plan.md).** Especially the business rules (§7), scope limits (§8) and success criteria (§11).
3. **The task in `backlog.md`.** Its description and **Done when** criteria define what to build.
4. **The existing code.** Follow its naming, structure and idioms.

## Workflow

1. **Pick one task.** Take the task you were given, or the next one in **Suggested order**. Work on one at a time.
2. **Check that it's ready.** Confirm it meets the PM's [Definition of Ready](pm.md#definition-of-ready) and that its dependencies are finished. If not, stop and report why.
3. **Read the sources.** Read the plan sections and decisions the task cites, along with the code it touches.
4. **Write the tests.** Turn each criterion into at least one test, and see the new tests fail where the behaviour doesn't exist yet.
5. **Implement.** Write the smallest change that meets the criteria.
6. **Run the checks.** Run everything under [Checks](#checks), not only the new tests.
7. **Hand over.** Finish with the [handover report](#handover-report) and leave the task open.

## Scope

- Change only what the task needs. If you notice other work, report it rather than including it.
- Don't build ahead for a later task, even if you know what it will need.
- Don't add anything in the backlog's **Out of scope** list.
- Commit or push only when asked, on a branch rather than `main`, and keep each branch to one task.

## Working with uv

Run everything through uv, and don't use `pip` or activate the virtual environment by hand.

| Purpose | Command |
|---|---|
| Install from the lockfile | `uv sync` |
| Add a dependency | `uv add <package>` |
| Add a dev dependency | `uv add --dev <package>` |
| Run the development server | `uv run python manage.py runserver` |
| Create migrations | `uv run python manage.py makemigrations` |
| Apply migrations | `uv run python manage.py migrate` |
| Run the tests | `uv run pytest` |
| Lint | `uv run ruff check .` |

Keep `pyproject.toml` and `uv.lock` together in the same change. Add a dependency only when the task names it or clearly needs it, and mention it in the report.

`pytest` arrives with T0.3 and `ruff` with T0.4. Before those tasks are finished, use `uv run python manage.py test` and `uv run python manage.py check`, and skip the lint step.

## Django rules

These apply to every task. Where a rule cites a source, check that source when a task depends on it.

- **App layout:** Put code in the app under `apps/` that owns the concept, and shared templates and static files in the top-level `templates/` and `static/`.
- **User model:** Refer to users through `settings.AUTH_USER_MODEL` or `get_user_model()`, never through `auth.User` (D8).
- **Permissions:** Enforce access on the server for every view, including POST requests. Hiding a link isn't protection.
- **Household isolation:** Scope every query for household data to the current user's household, so a member of another household can't read or change it.
- **State changes:** Change data only through POST requests with CSRF protection.
- **Time:** Store datetimes in UTC, and work out dates and schedules in the household's local time zone (§7.3).
- **Integrity:** Use database constraints and transactions where a rule must hold under concurrent requests. A check in a form or view isn't enough on its own.
- **History:** Don't hard-delete records that history depends on, such as chores (D2) and memberships (rotation algorithm).
- **Migrations:** Include the migrations for every model change, and don't edit a migration that has already been committed.
- **Secrets:** Read secrets and environment-specific settings from the environment. Add new names to `.env.example`, but never commit real values, `.env` or `db.sqlite3` (T0.1).

## Tests

Tests are part of the task, not a later phase. Phase 7 covers only cross-feature tests and the final check against the success criteria.

- **Location:** Put tests in `tests/` and shared factories in `tests/` too, as T0.3 sets up.
- **Coverage:** Cover the same areas the PM's [criteria](pm.md#acceptance-criteria-rules) must cover, wherever they apply: the main path, rejected actions, access for each type of user, repeats and concurrency, time, and history.
- **Behaviour:** Test what users and callers can observe, such as responses and saved data, rather than internal details.
- **Time:** Control the clock in time-dependent tests, and include a time zone other than UTC. Tests mustn't depend on when they run.
- **Bugs:** When fixing a bug, first add a test that fails because of it.
- **Failures:** Don't skip, weaken or delete a test to get a passing run. If a test seems wrong, explain why in the report.

SQLite doesn't exercise row locking the way PostgreSQL does. Concurrency tests for T2.2 and T4.3 only count as fully proven once they run on PostgreSQL (T8.1), so say so in the report if they have only run on SQLite.

## Checks

Before handing over, all of these must pass:

```bash
uv run python manage.py check
uv run python manage.py makemigrations --check
uv run ruff check .
uv run pytest
```

For anything a user sees, also run the app and try the changed pages by hand. If a check can't be run, say so in the report rather than implying it passed.

## When to escalate

Stop and ask rather than guess when:

- The task, plan and decisions disagree or don't answer a question about product behaviour.
- A criterion can't be met, can't be checked or seems wrong.
- The task would need to change a confirmed decision or the rotation algorithm.
- The task turns out to be much bigger than its size, or depends on unfinished work that isn't listed.

Product questions go to the PM, who takes them to the project owner when needed. Ask each one with the options and a recommendation. Technical choices that don't change product behaviour are yours to make, so note the important ones in the report.

## Handover report

Finish each task with this summary, and leave the boxes in `backlog.md` unticked:

```markdown
## Handover: T1.1 Task name

**Status:** Ready for verification | Blocked — <reason>

**Criteria:**
- <criterion as written> — `tests/test_file.py::test_name` passes
- <criterion as written> — checked by hand: <steps and result>
- <criterion as written> — not met: <why>

**Checks:** <each command under Checks, with its result, or why it wasn't run>
**Changes:** <main files, migrations and dependencies>
**Technical choices:** <important choices, or "None">
**Questions and follow-ups:** <open questions and out-of-scope findings, or "None">
```
