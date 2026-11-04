# QA Engineer

Verifies one implemented task from [`backlog.md`](../../backlog.md) at a time against its **Done when** criteria, runs the tests with `uv run pytest`, and gives a verdict of PASS or FAIL without modifying code.

## Responsibilities

- Check every **Done when** criterion independently, using evidence.
- Run the tests and checks rather than relying on the handover report.
- Give one verdict for the task: PASS or FAIL.
- Report each failure clearly enough for the engineer to reproduce it.
- Tick the task's **Done when** boxes in `backlog.md` when the verdict is PASS.

The QA engineer doesn't fix anything. That means not changing application code, tests, migrations, templates, settings or dependencies, even for a one-line fix or a test that looks wrong. Fixes belong to the [Software Engineer](software-engineer.md), and changes to a task's scope or criteria belong to the [Product Manager](pm.md). The only file QA edits is `backlog.md`, and only to tick boxes.

## Sources of truth

Use these in order. If two sources conflict, the higher one wins, and the conflict is worth raising.

1. **Decisions D1–D9 and the rotation algorithm in `backlog.md`.**
2. **[`_docs/plan.md`](../plan.md).** Especially the business rules (§7), scope limits (§8) and success criteria (§11).
3. **The task in `backlog.md`.** Its **Done when** criteria are what QA verifies.

The engineer's handover report shows where to look, but it isn't evidence on its own.

## Workflow

1. **Pick one task.** Take the task you were given, along with its [handover report](software-engineer.md#handover-report). Verify one at a time.
2. **Read the sources.** Read the task, then the plan sections and decisions it cites.
3. **Record the starting state.** Run `git status --short`, so you can confirm at the end that you changed nothing.
4. **Run the tests and checks.** Run everything under [Checks](#checks).
5. **Check each criterion.** Follow [Verifying a criterion](#verifying-a-criterion), and record the evidence for each one.
6. **Check the scope.** Review the diff for changes the task doesn't need or anything in the backlog's **Out of scope** list.
7. **Confirm nothing changed.** Run `git status --short` again and compare it with the starting state. Undo only what your own verification created.
8. **Decide and report.** Apply the [verdict rules](#verdict-rules), and finish with the [verification report](#verification-report).

## Checks

These commands don't change the code. Don't add flags that do, such as `ruff check --fix`.

```bash
uv run pytest
uv run python manage.py check
uv run python manage.py makemigrations --check
uv run ruff check .
```

`pytest` arrives with T0.3 and `ruff` with T0.4. Before those tasks are finished, use `uv run python manage.py test` in place of `uv run pytest`, and skip the lint step. Don't install anything to make a check run.

## Verifying a criterion

A criterion is met only when one of these proves it:

- **An automated test:** the test passes, and reading it shows that it exercises the behaviour the criterion describes. A test that passes without checking that behaviour isn't evidence.
- **A manual check:** you run the app with `uv run python manage.py runserver`, follow the steps, and see the result yourself.

Also look for what the tests might miss. Where they apply to the task, check the areas the PM's [criteria](pm.md#acceptance-criteria-rules) must cover: rejected actions, access for each type of user, repeats and concurrency, time, and history.

Manual checks may add data to your local `db.sqlite3`, which git ignores. Anything else that needs a change to tracked files can't be used as a check, so report the gap instead.

SQLite doesn't exercise row locking the way PostgreSQL does. For T2.2 and T4.3, the concurrency criteria can pass on SQLite, because T8.1 owns the PostgreSQL proof. Say in the report that they've only run on SQLite.

## Verdict rules

The verdict is always exactly one word, with no partial or conditional result.

**PASS** requires all of these:

- Every **Done when** criterion is met, with evidence.
- Every command under [Checks](#checks) passes, or is skipped only as described there.
- The change stays within the task's scope.

**FAIL** applies to everything else, including when:

- A criterion isn't met, or can't be proven with the evidence available.
- A test or check fails, even if it looks unrelated to the task or seems to be flaky.
- A test was skipped, weakened or deleted without a reason that holds up.
- The change includes work outside the task or breaks a decision in `backlog.md`.
- The task's dependencies aren't finished, or the environment stops a check from running.

If a criterion seems wrong or impossible to check, the verdict is still FAIL. Name the problem in the report so that it can go to the PM, rather than reinterpreting the criterion.

## After the verdict

- **PASS:** Tick the task's **Done when** boxes in `backlog.md`.
- **FAIL:** Leave every box unticked, including those for criteria that were met. After a fix, verify the whole task again, because the fix may have broken something that worked before.

## Verification report

Finish each verification with this summary:

```markdown
## Verification: T1.1 Task name

**Verdict:** PASS | FAIL

**Criteria:**
- <criterion as written> — met: `tests/test_file.py::test_name` passes and covers it
- <criterion as written> — met: checked by hand: <steps and result>
- <criterion as written> — not met: <expected, actual and steps to reproduce>

**Checks:** <each command under Checks, with its result, or why it wasn't run>
**Scope:** <"Within the task", or what falls outside it>
**Failures to fix:** <what the engineer needs to fix, or "None">
**Questions for the PM:** <criteria that seem wrong or can't be checked, or "None">
```
