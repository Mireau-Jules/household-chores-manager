# Household Chores Manager — MVP Backlog

Source: [`_docs/plan.md`](_docs/plan.md). References such as §7.5 point to sections of that plan.

**Current state:** the Django project and five empty apps exist (`accounts`, `households`, `chores`, `assignments`, `notifications`). There are no models, views, URLs or migrations yet.

**Key**

- **Size:** S = up to half a day, M = about a day, L = 2 days or more
- **Priority:** P0 = required for the MVP success criteria, P1 = needed for a complete MVP, P2 = polish
- **Depends on:** tasks that must be finished first

## Overview

| Epic | Plan phase | Goal | Tasks | Sizes |
|---|---|---|---|---|
| E0 Foundation | Added | Make the project ready for feature work | 5 | 4 S, 1 M |
| E1 Accounts and Households | Phase 1 | Users can register and create a household | 6 | 3 S, 3 M |
| E2 Invitations and Members | Phase 2 | Users can join, leave and transfer the admin role | 6 | 2 S, 4 M |
| E3 Chores | Phase 3 | Admins can manage daily chores | 3 | 1 S, 2 M |
| E4 Rotation and Scheduling | Phase 4 | Assignments are generated automatically and fairly | 6 | 3 S, 2 M, 1 L |
| E5 Dashboards and Tracking | Phase 5 | Members can see and complete their chores | 3 | 1 S, 2 M |
| E6 History and Notifications | Phase 6 | Members can see history and get notifications | 4 | 1 S, 3 M |
| E7 Verification | Phase 7 | The MVP is proven against its success criteria | 3 | 1 S, 1 M, 1 L |
| E8 Production Readiness | Added | The app runs on Render with PostgreSQL and a real cron job | 4 | 3 S, 1 M |

**Changes from the plan's phases**

- **E0 and E8 are new.** The plan has no setup or deployment phase, but automatic generation needs a hosted cron job and production uses PostgreSQL. E0–E7 run entirely on local SQLite, without Docker or PostgreSQL.
- **Tests are written with each task.** Phase 7 now covers only cross-feature tests and the final check against the success criteria.
- **No `requirements/` folder.** `pyproject.toml` and `uv.lock` already cover this.

## Decisions

The plan left these points open or in tension. All nine were confirmed on 2026-11-03, and the tasks below follow them.

| # | Question | Decision | Affects |
|---|---|---|---|
| D1 | **How do per-chore rotation and even distribution work together?** If every chore simply moves to the next member, they can stay in step and give one person every chore each day (§7.5). | Each chore keeps its own position, and generation picks the next member in that chore's cycle with the fewest assignments so far that day. See [the rotation algorithm](#rotation-algorithm). | T4.2 |
| D2 | **What does deleting a chore do?** Hard deletion would conflict with preserving history (§7.8). | Soft-delete it. It stops generating, and existing assignments, including pending ones, stay as they are. | T3.1, T3.2 |
| D3 | **What happens if generation is missed, for example during a cron outage?** | A household is due whenever its local time is at or past the generation time and today has no run. Missed earlier days are not backfilled. | T4.3 |
| D4 | **What happens when the generation time or time zone changes after today's run?** | There is no second run for that local date, and the new settings apply from the next one. | T4.3, T1.6 |
| D5 | **When are pending reminders sent?** §7.9 doesn't say. | During each daily run, send each member one summary if they have pending assignments from earlier days. | T6.3 |
| D6 | **Where do notifications appear?** They aren't among the eight screens in §6. | A navigation badge showing the unread count, plus a list panel on the Household Dashboard, so there is no ninth screen. | T6.4 |
| D7 | **Can an admin who is the only member ever leave?** There is nobody to transfer the role to (§7.1), and the plan has no household deletion. | Block leaving in the MVP and show an explanation. Add household deletion later. | T2.5 |
| D8 | **How do people log in?** | Use email and password, with a custom user model built on Django's built-in authentication. | T0.2, T1.1 |
| D9 | **Which environments will the app run in?** | SQLite for local development now. A Docker image on Render with PostgreSQL for production later. | T0.1, T8.1–T8.3 |

## E0 — Foundation

### T0.1 Configure the project · P0 · S
- Add `templates/` to `TEMPLATES['DIRS']`, and set `STATICFILES_DIRS` and `STATIC_ROOT`.
- Read `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` and `DATABASE_URL` from the environment, and add `.env.example`.
- Use `dj-database-url` to parse `DATABASE_URL`, falling back to the local SQLite file when it isn't set (D9).

**Done when:**
- [ ] The hard-coded `SECRET_KEY` is gone **before the first commit of `config/`**, because that file is currently untracked.
- [ ] `manage.py check` passes using only values from `.env.example`.
- [ ] Local development uses SQLite with no `DATABASE_URL` set.
- [ ] `USE_TZ = True` and `TIME_ZONE = 'UTC'` are still set (§7.3).

### T0.2 Add a custom user model · P0 · S
Depends on: T0.1

- Create `accounts.User` from `AbstractUser`, with a unique email as the login field (D8).
- Set `AUTH_USER_MODEL`.

**Done when:**
- [ ] This is the first migration applied. Swapping the user model later is difficult, so it has to happen before any other app migrates.

### T0.3 Set up the test tools · P0 · S
- Add `pytest`, `pytest-django` and `factory-boy` as uv dev dependencies.
- Add pytest settings to `pyproject.toml`, and shared factories to `tests/`.

**Done when:**
- [ ] `uv run pytest` finds and runs a smoke test.

### T0.4 Set up code quality and CI · P1 · S
Depends on: T0.3

- Configure `ruff`.
- Add a GitHub Actions workflow that runs lint, `manage.py makemigrations --check` and pytest.

**Done when:**
- [ ] CI runs on every pull request and fails if a migration is missing.

### T0.5 Build the base layout · P0 · M
Depends on: T0.1

- Create `base.html` with navigation, Django messages and a mobile-friendly stylesheet.
- Add 403 and 404 pages.

**Done when:**
- [ ] Navigation adapts to the user's state: logged out, no household, member or admin.

## E1 — Accounts and Households

### T1.1 Registration, login and logout · P0 · M
Depends on: T0.2, T0.5

- Build Screen 1 using Django's auth views and a registration form.
- Honour a safe `next` redirect, which the invitation flow needs (T2.3).

**Done when:**
- [ ] Users can register, log in and log out, and passwords go through the configured validators.
- [ ] Duplicate emails are rejected regardless of letter case.
- [ ] An external `next` URL is ignored.

### T1.2 Household and membership models · P0 · M
Depends on: T0.2

- `Household`: name, IANA `timezone`, `generation_time`.
- `Membership`: user, household, role, `is_active`, `joined_at`, `left_at`. Rows are deactivated and never deleted, so history and rotation references stay valid.
- Add database constraints as described below.

**Done when:**
- [ ] A partial unique constraint allows one active membership per user (§7.1).
- [ ] A partial unique constraint allows one active admin per household (§7.1).
- [ ] Invalid time zone names are rejected.

### T1.3 Household access control · P0 · S
Depends on: T1.2

- Add `household_member_required` and `household_admin_required` helpers.
- Fetch data through the current user's household, never through a household ID from the URL.

**Done when:**
- [ ] Other households' data returns 404, a member using an admin action gets 403, and users without a household are redirected to Screen 2.

### T1.4 Create or Join screen · P0 · M
Depends on: T1.2, T1.3, T0.5

- Build Screen 2 with household name, time zone and generation time. T2.3 adds the option to join with an invitation link.
- Creating a household also makes the creator its admin, in a single transaction.

**Done when:**
- [ ] A user who already has a household can't create another.
- [ ] Time zones are chosen from a list of valid IANA names.

### T1.5 Show times in the household's time zone · P0 · S
Depends on: T1.2

- Add middleware that activates the current household's time zone for each request.

**Done when:**
- [ ] Timestamps display in household time while the database stores UTC (§7.3).

### T1.6 Household Settings screen · P0 · S
Depends on: T1.3, T1.5

- Build Screen 7, where the admin edits the name, time zone and generation time.

**Done when:**
- [ ] The screen is admin-only.
- [ ] Changes don't cause a second run for the current local date (D4).

## E2 — Invitations and Members

### T2.1 Invitation model and creation · P0 · S
Depends on: T1.3

- `Invitation`: household, random token from `secrets`, `created_by`, `expires_at` (7 days), `used_at`, `used_by`.
- Add an admin action that generates a copyable link.

**Done when:**
- [ ] Only admins can generate links (§7.10).
- [ ] Tokens can't be guessed.

### T2.2 Invitation acceptance service · P0 · M
Depends on: T2.1

- Create `accept_invitation(token, user)`, using an atomic conditional update so a link can be used only once.

**Done when:**
- [ ] Expired, used and unknown links are rejected with a clear reason (§7.10).
- [ ] A user who is already in a household is rejected and the link stays valid.
- [ ] Two simultaneous attempts produce exactly one membership.

### T2.3 Invitation landing flow · P0 · M
Depends on: T2.2, T1.1

- Build `/invite/<token>/`, which shows the household name and asks the user to confirm joining.
- Send logged-out users through login or registration, then return them to the invitation.
- Add a field to Screen 2 for pasting an invitation link.

**Done when:**
- [ ] Joining happens only on POST, so link previews can't use up an invitation.
- [ ] A brand-new user can go from the link to membership without losing the invitation.

### T2.4 Member Management screen · P0 · M
Depends on: T1.3

- Build Screen 6, showing active members and their roles for everyone in the household.
- Admins also get the transfer control. T2.5 adds the leave and remove controls.

**Done when:**
- [ ] Controls are hidden from members, and the server also rejects their requests.
- [ ] Former members aren't listed as active.

### T2.5 Leave and remove service · P0 · M
Depends on: T1.2, T4.1

- Create one `deactivate_membership` service for both leaving and removal.
- In one transaction, deactivate the membership and mark its pending assignments as `cancelled`, with no reassignment (§7.5).
- Add the leave control for members and the remove control for admins.

**Done when:**
- [ ] An admin can't leave or be removed without transferring the role first, and a sole admin sees an explanation (D7).
- [ ] Completed assignments are unchanged.
- [ ] The user can then create or join another household.

### T2.6 Transfer the admin role · P0 · S
Depends on: T2.4

- In one transaction, demote the current admin first, then promote the new one, so the unique constraint isn't violated.

**Done when:**
- [ ] The target must be an active member of the same household.
- [ ] There is exactly one admin afterwards, and both users stay in the rotation.

## E3 — Chores

### T3.1 Chore model · P0 · S
Depends on: T1.2

- `Chore`: household, name, optional description, `is_active`, `last_assigned_membership` (nullable).

**Done when:**
- [ ] Active chore names are unique within a household, ignoring letter case and surrounding spaces.
- [ ] Blank names are rejected.

### T3.2 Chore create, edit and delete · P0 · M
Depends on: T3.1, T1.3

- Build the admin's create, edit and delete actions, using POST with a confirmation step for deletion.
- Deleting is a soft delete (D2).

**Done when:**
- [ ] Non-admins are rejected, and chores from other households return 404.
- [ ] A deleted chore's past assignments keep its name in history.

### T3.3 Chore Management screen · P0 · M
Depends on: T3.2

- Build Screen 5 with the list of active chores for the household.
- Include a useful empty state for new households.

**Done when:**
- [ ] Admins see the controls, while members get a read-only list.

## E4 — Rotation and Scheduling

### T4.1 Assignment model · P0 · S
Depends on: T3.1, T1.2

- `Assignment`: chore, `assignee` (Membership), `assignment_date`, status (`pending`, `completed`, `cancelled`), `completed_at`.
- `GenerationRun`: household, `local_date`, `created_at`.
- Use `PROTECT` on foreign keys so history can't be deleted by accident.

**Done when:**
- [ ] Uniqueness is enforced on `(chore, assignment_date)` and `(household, local_date)` in the database.
- [ ] A check constraint requires `completed_at` to be set only when the status is `completed`.

### T4.2 Rotation algorithm · P0 · L
Depends on: T4.1

- Write a function that plans a day's assignments from chores and active memberships, without touching the database, so it is easy to test. It follows [the rotation algorithm](#rotation-algorithm).

**Done when:**
- [ ] One member's assignment count for any day differs from another's by at most 1.
- [ ] Each chore moves through all active members over time, and the admin is included.
- [ ] With fewer chores than members, assignments still reach every member over time.
- [ ] A new member enters the cycle at the next run without resetting positions.
- [ ] Rotation continues correctly when the last assigned member has left, and inactive members are never chosen.
- [ ] Tests cover the combinations in the simulation below.

### T4.3 Per-household generation service · P0 · M
Depends on: T4.2

- Create `generate_for_household(household, now)`. Passing in `now` makes tests simple.
- In one transaction: convert `now` to local time, create the `GenerationRun`, create assignments and update chore positions. T6.3 adds notifications to this transaction.

**Done when:**
- [ ] Running it twice for one local date creates nothing new, including when two runs overlap (§7.2).
- [ ] Earlier pending assignments aren't changed (§7.6).
- [ ] An error rolls back the whole household's run, including its `GenerationRun`, so the next cron run retries it.
- [ ] Earlier days aren't backfilled (D3).

### T4.4 Find households that are due · P0 · S
Depends on: T4.3

- Compare each household's local time and date with its settings, and check for an existing `GenerationRun` (D3).

**Done when:**
- [ ] Tests cover households on either side of midnight UTC.
- [ ] Tests cover daylight saving changes in `America/New_York`, including a generation time inside the skipped or repeated hour.
- [ ] The server's date is never used (§7.3).

### T4.5 `generate_assignments` management command · P0 · S
Depends on: T4.4

- Add the command for cron to run every five minutes.

**Done when:**
- [ ] One household's failure is logged without stopping the others, and the command then exits non-zero.
- [ ] The command logs how many households were processed, skipped and failed.
- [ ] Running it again immediately changes nothing.

### T4.6 Membership change integration tests · P0 · M
Depends on: T4.5, T2.3, T2.5

- Run generation over several days while members join and leave.

**Done when:**
- [ ] All the "Membership changes" rules in §7.5 pass across real generated days.

## E5 — Dashboards and Tracking

### T5.1 Complete an assignment · P0 · S
Depends on: T4.1, T1.3

- Create a POST-only action using a conditional update from `pending` to `completed` that sets `completed_at`.

**Done when:**
- [ ] A second attempt changes nothing and keeps the original timestamp (§7.7).
- [ ] Other members, including the admin, can't complete someone else's assignment (§7.7).
- [ ] Cancelled assignments can't be completed.

### T5.2 Personal Chore Dashboard · P0 · M
Depends on: T5.1, T1.5

- Build Screen 4 with sections for today's chores and pending chores from earlier days, showing each one's original date.
- "Today" means the household's local date.

**Done when:**
- [ ] It shows only the logged-in member's assignments.
- [ ] Several pending assignments for the same chore on different days all appear (§7.6).
- [ ] New users see a useful message before their first generation.

### T5.3 Household Dashboard · P0 · M
Depends on: T4.1, T1.5, T0.5

- Build Screen 3, showing today's assignments for all members with their status, plus the household's pending count.

**Done when:**
- [ ] It works for all active members and shows no completion control for other members' chores.
- [ ] Household queries don't grow with the number of assignments (no N+1 queries).

## E6 — History and Notifications

### T6.1 Activity History screen · P0 · M
Depends on: T4.1, T1.5

- Build Screen 8 with chore name, member, assignment date, completion date and status, with pagination.

**Done when:**
- [ ] Cancelled and completed entries are visibly different (§7.8).
- [ ] Records of former members and deleted chores still appear (§7.8).
- [ ] Only active members can open it, and it shows only their household.

### T6.2 Notification model · P0 · S
Depends on: T1.2

- `Notification`: recipient, household, type (`new_assignments`, `pending_reminder`), message, `created_at`, `read_at`.

**Done when:**
- [ ] Unread notifications can be queried efficiently using an index.

### T6.3 Create notifications during generation · P0 · M
Depends on: T6.2, T4.3

- During the T4.3 transaction, create one "new assignments" summary per member who received chores, and one reminder per member with earlier pending assignments (D5).

**Done when:**
- [ ] Inactive members receive nothing.
- [ ] Each member gets at most one of each type per household day, including on retried runs.
- [ ] Members without new or pending chores get nothing.

### T6.4 Notification display and read status · P1 · M
Depends on: T6.2, T5.3

- Add the unread badge through a context processor, and the list panel on the Household Dashboard (D6).
- Add POST actions for marking one or all notifications as read.

**Done when:**
- [ ] Users can see and change only their own notifications.
- [ ] The badge count updates after notifications are marked as read.

## E7 — Verification

### T7.1 Permission and data isolation tests · P0 · M
Depends on: E1–E6

- Check every URL against each kind of user: logged out, no household, member, admin and member of another household.

**Done when:**
- [ ] A table-driven test covers every route, and a new URL fails the test until it is added.

### T7.2 End-to-end workflow test · P0 · L
Depends on: E1–E6

- Using Django's test client, follow §5 in full: register, create a household, invite, join, add chores, configure settings, generate, complete, then check history and notifications.
- Advance time across several simulated days.

**Done when:**
- [ ] The test passes on both SQLite and PostgreSQL.

### T7.3 Success criteria check · P0 · S
Depends on: T7.1, T7.2, T8.3

- Go through each item in §11 by hand on the deployed app, and record the result in the README or a release checklist.

**Done when:**
- [ ] All 17 criteria in §11 are checked, with any failures logged as new tasks.

## E8 — Production Readiness

### T8.1 Support PostgreSQL · P0 · S
Depends on: T0.1

- Add `psycopg`, so that setting `DATABASE_URL` is all it takes to switch to PostgreSQL.
- Add a PostgreSQL job to CI, alongside the existing SQLite run.

**Done when:**
- [ ] All migrations and tests pass on PostgreSQL.
- [ ] The concurrency tests for T2.2 and T4.3 run on PostgreSQL, because SQLite doesn't exercise row locking the same way.

### T8.2 Build the Docker image · P0 · S
Depends on: T8.1

- Add a `Dockerfile` that installs from `uv.lock`, collects static files with `whitenoise` and starts `gunicorn` as a non-root user.
- Add a `.dockerignore` that excludes `.env`, `db.sqlite3`, `.venv` and `.git`.

**Done when:**
- [ ] The image builds and serves the app when given a PostgreSQL `DATABASE_URL`.
- [ ] No secrets or local database are included in the image.

### T8.3 Deploy to Render · P0 · M
Depends on: T8.2, T4.5

- Define a Docker web service, a PostgreSQL database and a cron job in `render.yaml`, with the cron job using the same image.
- Schedule `generate_assignments` with `*/5 * * * *`, which Render evaluates in UTC. Household local time is handled by the command (§7.3).
- Run migrations as part of each deploy.
- Configure secure cookies, HTTPS settings, `ALLOWED_HOSTS` and `SECURE_PROXY_SSL_HEADER`, because Render handles HTTPS at its proxy.
- Choose Render plans for the web service, database and cron job, checking current limits and prices first. Production data must not depend on a time-limited free database.

**Done when:**
- [ ] `manage.py check --deploy` passes with production settings.
- [ ] Data survives a redeploy, which confirms production is on PostgreSQL and not SQLite on the container's disk.
- [ ] A household on the deployed app gets assignments at its configured local time without manual action.
- [ ] A failed cron run is visible in Render's logs.

### T8.4 Write the README · P1 · S
Depends on: T8.3

- Cover local setup with uv and SQLite, running tests and generation by hand, environment variables, the Docker image and the Render deployment.

**Done when:**
- [ ] Someone new can run the app and its tests by following only the README.

## Suggested order

Each milestone ends with something you can demonstrate.

| Milestone | Tasks | Demo |
|---|---|---|
| **M1 Skeleton** | T0.1–T0.3, T0.5, T0.4 | The project runs, and tests and CI pass |
| **M2 Household** | T1.1–T1.6 | Register, create a household and change its settings |
| **M3 Membership** | T2.1–T2.4, T2.6 | Invite someone, have them join and transfer the admin role |
| **M4 Chores** | T3.1–T3.3 | The admin manages the chore list |
| **M5 Rotation** | T4.1–T4.5, T2.5, T4.6 | The command generates fair assignments |
| **M6 Daily use** | T5.1–T5.3 | Members see and complete their chores |
| **M7 Feedback** | T6.1–T6.4 | History and notifications work |
| **M8 Release** | T8.1, T7.1, T7.2, T8.2, T8.3, T7.3, T8.4 | The deployed app passes the §11 check |

T2.5 moves to M5 because cancelling assignments needs the `Assignment` model from T4.1.

**Highest-risk tasks:** T4.2, T4.3 and T4.4 hold most of the logic that is hard to get right.

**Testing generation locally:** until M8 there is no cron job, so run `manage.py generate_assignments` by hand.

## Rotation algorithm

This is the confirmed answer to D1.

```text
members = active memberships, ordered by id     # new members join the end of the cycle
loads   = 0 for every member                    # assignments so far today

for chore in active chores, ordered by id:
    cycle  = members, starting just after the chore's last_assigned_membership
             (the first member if it has none)
    chosen = the first member in cycle with the lowest load
    create the assignment for chosen
    loads[chosen] += 1
    chore.last_assigned_membership = chosen
```

Storing the last membership rather than a list index keeps positions valid when people join or leave. Membership rows are never deleted, so "just after" still works when that member has left.

**Simulation:** I ran this for 365 days, without membership changes, on every combination of 1–8 members and 1–12 chores.

| Measure (highest difference between members) | Each chore simply moves to the next member | Chosen algorithm |
|---|---|---|
| Assignments on any one day, worst case across all combinations | 12 | 1 |
| Total over the year, 3 chores and 3 members | 3 | 0 |
| Total over the year, 5 chores and 2 members | 5 | 1 |
| Total over the year, 10 chores and 4 members | 10 | 1 |
| Total over the year, worst case across all combinations | 12 | 3 |
| One chore's total over the year, worst case across all combinations | 1 | 1 |

With the simple approach, 3 chores and 3 members means one person gets all three chores every day. The chosen algorithm's worst yearly difference of 3 appeared only with 8 members. Membership changes weren't simulated, so T4.6 covers those.

## Out of scope

These are deferred by §8 and shouldn't be added to the MVP:

- Gamification, expense management, chat, AI recommendations, photo verification and advanced analytics
- Automatic reassignment of incomplete chores
- Weekly, monthly and one-time chores
- Email and push notifications
- Membership in several households, and mobile apps
- Celery and Redis (§7.2)
