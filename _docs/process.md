# Development Process

How tasks in [`backlog.md`](../backlog.md) move from groomed to verified, and how the orchestrator coordinates the [Product Manager](team/pm.md), [Software Engineer](team/software-engineer.md) and [QA Engineer](team/qa-engineer.md).

This document covers who works next and what they receive. The role files define how each role does its work, and they take priority over this document on that.

## Participants

| Participant | Does | Doesn't |
|---|---|---|
| **Project owner** | Confirms decisions, answers product questions, approves commits and merges | Need to be involved in technical choices |
| **Orchestrator** | Chooses the next task, starts each role, passes reports between them, keeps the loop moving | Write code, groom tasks, tick boxes, give verdicts or answer product questions |
| **PM** | Grooms tasks and writes their **Done when** criteria | See [PM](team/pm.md) |
| **Engineer** | Implements and tests one task | See [Software Engineer](team/software-engineer.md) |
| **QA** | Verifies one task and gives a verdict | See [QA Engineer](team/qa-engineer.md) |

The orchestrator is usually the main agent session, with each role running as a separate agent. If the orchestrator finds itself doing a role's work, it should start that role instead.

## Rules

- **One task at a time.** All roles share one working tree, and QA compares `git status` before and after, so tasks can't overlap. Grooming is the exception: the PM can groom several tasks in one session.
- **Separate roles.** The engineer and QA never run as the same agent. Start QA fresh, with the task ID and the handover report only, so that its verdict stays independent.
- **Only QA closes a task.** A task is finished when QA gives a PASS and ticks all of its **Done when** boxes.
- **The backlog holds the state.** Don't add status fields or tracking files. See [Task states](#task-states).
- **Questions go up, not around.** Only the project owner can answer product questions or change decisions. The orchestrator passes them on and doesn't choose an answer, even when one seems obvious.

## Task states

| State | How to tell | Next role |
|---|---|---|
| **Not ready** | The PM hasn't confirmed it against the [Definition of Ready](team/pm.md#definition-of-ready) | PM |
| **Ready** | The PM's latest [grooming report](team/pm.md#grooming-report) lists it under **Ready** | Engineer |
| **In progress** | The engineer is working on it, or its changes are uncommitted and it has no handover report | Engineer |
| **In verification** | The [handover report](team/software-engineer.md#handover-report) says "Ready for verification" | QA |
| **Blocked** | A report names a question or blocker that nobody has resolved | Project owner, through the PM |
| **Finished** | All of its **Done when** boxes are ticked | None |

Unticked boxes don't show that a task is groomed, because tasks already had draft criteria before grooming started.

## Orchestrator loop

```text
confirm with the project owner whether commits and merges need approval each time

while Suggested order has an unfinished task:
    task = next unfinished task in Suggested order

    if task isn't ready:
        run PM on the unfinished tasks in task's milestone
        if the PM reports task as blocked:
            ask the project owner, have the PM record the answer, and start again
        continue

    fails = 0
    run Engineer on task
    loop:
        if the handover report says Blocked:
            resolve it through the PM or the project owner, then run Engineer on task
            continue

        run QA on task, with the handover report

        if the verdict is PASS:
            break

        fails += 1
        if fails == 3:
            stop and escalate to the project owner
        if the report has questions for the PM:
            run PM on those questions, and resolve any blocker with the project owner
        run Engineer on task, with the verification report

    commit and merge task, with approval if it's needed
    if task was the last in its milestone:
        report the milestone's demo to the project owner, and wait for them to continue
```

The loop ends when every task is finished, which includes the §11 check in T7.3.

## Handoffs

Each role gets only what it needs, and it reads the sources itself.

| Step | Start with | Returns | What happens next |
|---|---|---|---|
| **Groom** | [PM role](team/pm.md), plus the milestone or task range | Grooming report | **Ready** tasks can start, and **Blocked** tasks and **Decisions needed** go to the project owner |
| **Implement** | [Engineer role](team/software-engineer.md), plus the task ID | Handover report | "Ready for verification" goes to QA, and "Blocked" goes to the PM |
| **Verify** | [QA role](team/qa-engineer.md), plus the task ID and handover report | [Verification report](team/qa-engineer.md#verification-report) | PASS closes the task, and FAIL goes back to the engineer |
| **Fix** | Engineer role, plus the task ID and verification report | New handover report | Goes to QA, which verifies the whole task again |

## When QA gives a FAIL

Route each part of the verification report to the role that owns it:

| The report says | Goes to | Then |
|---|---|---|
| **Failures to fix** lists code or test problems | Engineer | QA verifies the whole task again |
| **Questions for the PM** says a criterion is wrong or can't be checked | PM | The engineer makes any changes needed, then QA verifies the whole task again |
| The problem is a missing dependency or a broken environment | Orchestrator | Fix the order or environment through the role that owns it, then QA verifies again |
| The failure can't be fixed without changing a decision | Project owner, through the PM | The loop waits for an answer |

The engineer and QA don't negotiate a verdict, and the engineer doesn't rewrite criteria to get a PASS. After the third FAIL on one task, the loop stops, because the problem is probably in the task rather than the code. Give the project owner the reports and a recommendation, such as splitting the task.

## When to involve the project owner

Stop the loop and ask when:

- A role reaches one of its escalation conditions, such as those in the [PM's list](team/pm.md#when-to-escalate).
- One task has failed verification three times.
- A commit or merge needs approval.
- A milestone is finished and its demo is ready.

Ask each question with the affected tasks, the options and a recommendation. After a product answer, the PM records it in `backlog.md` before work continues. A new decision takes the next D number, as described in [Updating the backlog](team/pm.md#updating-the-backlog).

## Commits

Nothing is committed or pushed without the project owner's approval, either each time or as standing approval given at the start of the loop.

Once a task has a PASS:

1. The engineer commits the task's changes on a branch for that task, together with QA's ticks in `backlog.md`.
2. The orchestrator merges the branch into `main`, so the next task starts from a clean tree and QA sees only that task's changes.

If commits aren't approved yet, the loop waits here rather than starting another task on top of uncommitted work.

**First task:** `config/`, `apps/` and the rest of the Django project are still untracked, so T0.1 has no diff for QA to review, and QA reads the files directly. The hard-coded `SECRET_KEY` must be gone before `config/` is first committed (T0.1). That means committing the project only after T0.1 has a PASS.

## Resuming after an interruption

Reports only exist in the session that produced them, so work out where things stand from the repository:

1. Run `git status --short` and `git branch`, and find the next unfinished task in **Suggested order**.
2. **If the tree is clean,** run the PM on that task. Grooming a task that's already ready should confirm it with no changes.
3. **If there are uncommitted changes,** run the engineer on that task to finish the work and write a new handover report, then continue with QA.
