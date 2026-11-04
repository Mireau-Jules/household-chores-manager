# Household Chores Manager — Agent Guide

A Django web app that coordinates household chores through automatically generated daily assignments and fair rotation.

## Project documents

| Document | Use it for |
|---|---|
| [`_docs/plan.md`](_docs/plan.md) | Product scope, business rules (§7), out-of-scope features (§8) and success criteria (§11) |
| [`_docs/process.md`](_docs/process.md) | The workflow and orchestrator loop between the PM, Software Engineer and QA Engineer |
| [`backlog.md`](backlog.md) | Tasks, their **Done when** criteria, confirmed decisions D1–D15, the rotation algorithm and the suggested order |

Decisions D1–D15 and the rotation algorithm in `backlog.md` take priority over `_docs/plan.md`, which takes priority over the rest of the backlog. Only the project owner can confirm a new decision or change an existing one.

## Team roles

Read the role file for the work you've been given, and stay within that role.

| Role | Does | Doesn't |
|---|---|---|
| [Product Manager](_docs/team/pm.md) | Grooms tasks and writes their **Done when** criteria | Write code or confirm that criteria are met |
| [Software Engineer](_docs/team/software-engineer.md) | Implements and tests one groomed task at a time, then hands it over | Tick **Done when** boxes or edit a task's scope |
| [QA Engineer](_docs/team/qa-engineer.md) | Verifies one task at a time and gives a PASS or FAIL verdict | Change anything except ticking boxes in `backlog.md` |

## Commands

Run everything through uv. Don't use `pip` or activate the virtual environment by hand.

```bash
# Install dependencies from the lockfile
uv sync

# Create your local settings (every manage.py command needs them)
cp .env.example .env

# Run the Django development server
uv run python manage.py runserver

# Run the tests
uv run python manage.py test
```

Once T0.3 adds pytest to the project, run the tests with `uv run pytest` instead.
