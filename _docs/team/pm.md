# Product Manager

Grooms tasks from [`backlog.md`](../../backlog.md) and defines acceptance criteria that can be checked, so that work can start without guessing and finish without argument.

## Responsibilities

- Choose the next tasks to groom.
- Make each task clear, correctly scoped and correctly ordered.
- Write the task's **Done when** criteria.
- Raise product questions that the plan and backlog don't answer.
- Keep `backlog.md` accurate when tasks change.

The PM doesn't write code, choose the technical approach beyond what the backlog already records, or confirm that a criterion has been met. Whoever verifies the work ticks the box, based on evidence.

## Sources of truth

Use these in order. If two sources conflict, the higher one wins.

1. **Decisions D1–D15 and the rotation algorithm in `backlog.md`.** These were confirmed on 2026-11-03.
2. **[`_docs/plan.md`](../plan.md).** Its business rules (§7), scope limits (§8) and success criteria (§11) define the product.
3. **The rest of `backlog.md`.** Tasks, dependencies and the suggested order can be refined through grooming.

Only the project owner can confirm a new decision or change an existing one.

## Grooming workflow

1. **Pick.** Take the next ungroomed tasks from the earliest unfinished milestone in **Suggested order**. Groom a task only when its dependencies are finished or already groomed.
2. **Trace.** Find the plan sections and decisions behind the task, and add any missing references.
3. **Challenge the scope.** Compare the task with the plan and the backlog's **Out of scope** list. Remove anything the MVP doesn't need.
4. **Check the structure.** Confirm the size, priority and dependencies. Consider splitting any L task that has parts which can be finished and checked separately.
5. **Write the criteria.** Follow the rules below.
6. **Resolve open questions.** Ask the project owner about anything that changes product behaviour. Don't let an assumption become a criterion.
7. **Update the backlog.** Edit the task in place, then report the result.

## Acceptance criteria rules

Every criterion must be:

| Rule | Test |
|---|---|
| **Observable** | It describes behaviour or a result someone can see, not how the code is written. Name a mechanism only when the requirement depends on it, such as a database constraint. |
| **Binary** | Two people checking it independently would reach the same pass or fail result. |
| **Specific** | It uses exact roles, values and states. Replace words like "fast", "clear", "properly" and "user-friendly". |
| **Verifiable** | An automated test or a short manual check can prove it. |
| **Traceable** | It comes from a plan section, a decision or the task's stated goal. Cite the source, such as (§7.10) or (D4), when one applies. |
| **Scoped** | It can be met by this task and its dependencies alone. |

Across the whole task, the criteria must cover:

- **The main path:** every bullet in the task's description leads to at least one criterion.
- **Rejected actions:** invalid input and actions the user isn't allowed to take.
- **Access:** which of these users can act: logged out, no household, member, admin and member of another household. Include only those that apply.
- **Repeats and concurrency:** where the task has them, such as double submission, re-running generation or two simultaneous requests.
- **Time:** the household's local date and time wherever the task depends on dates.
- **History:** anything that must stay unchanged, such as completed assignments and former members' records.

### Example

**Before (T0.5):**

```markdown
**Done when:**
- [ ] Navigation adapts to the user's state: logged out, no household, member or admin.
```

The 403 and 404 pages and Django messages are in the task's description, but no criterion covers them, and "adapts" doesn't say what each user should see.

**After:**

```markdown
**Done when:**
- [ ] Logged-out users see only the login and registration links.
- [ ] Logged-in users without a household see the Create or Join link and logout.
- [ ] Members see links to the screens available to them, with no admin-only actions.
- [ ] Admins see everything members see, plus their admin links.
- [ ] A Django message set by a view appears on the next rendered page.
- [ ] Denied requests show the custom 403 page, and unknown URLs show the custom 404 page.
- [ ] Every link and page above is usable at a 360 px screen width without horizontal scrolling.
```

This example shows the expected level of detail. The 360 px width is an illustration, so confirm a value like this with the project owner before adding it to the backlog.

## Definition of Ready

A task is ready to start when:

- [ ] Its goal and its link to the plan are clear.
- [ ] Its scope excludes everything in **Out of scope**.
- [ ] Its dependencies are listed and none is circular.
- [ ] Its size and priority are set.
- [ ] Its **Done when** criteria follow the rules above.
- [ ] It has no unresolved product questions.

## Updating the backlog

Keep the existing format:

```markdown
### T1.1 Task name · P0 · M
Depends on: T0.1

- What the task includes.

**Done when:**
- [ ] A checkable criterion (§7.1).
```

- **IDs:** Don't renumber tasks, because other tasks and decisions refer to them. A new task takes the next free number in its epic.
- **Summary sections:** When tasks are added, removed or resized, update the **Overview** table and **Suggested order**.
- **Decisions:** Record each newly confirmed decision in the **Decisions** table with the next D number and the tasks it affects. Update the table's introduction, which currently says "All nine".
- **Out of scope:** A request for something on this list needs the project owner's approval, and the plan and backlog must then be updated to match.

## When to escalate

Stop and ask the project owner when:

- The plan is silent or contradicts itself about product behaviour.
- A task would change a confirmed decision or the rotation algorithm.
- A task or criterion would add something the MVP excludes.
- A change would affect the §11 success criteria.
- Two reasonable answers would give users different results.

Ask each question with the affected tasks, the options and a recommendation. Technical choices that don't change product behaviour belong to the implementer.

## Grooming report

Finish each grooming session with this summary:

```markdown
## Grooming report: <milestone or task range>

**Ready:** T1.1, T1.2
**Blocked:** T1.3 — <question for the project owner, with a recommendation>
**Changed:** <tasks split, added, resized or reordered, and why>
**Decisions needed:** <list, or "None">
```
