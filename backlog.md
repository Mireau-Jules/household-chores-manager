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
| E0 Foundation | Added | Make the project ready for feature work | 5 | 5 S |
| E1 Accounts and Households | Phase 1 | Users can register and create a household | 7 | 4 S, 3 M |
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

The plan left these points open or in tension. All fifteen were confirmed on 2026-11-03, and the tasks below follow them.

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
| D10 | **What does "mobile-friendly" mean?** The plan doesn't set a width. | Pages have no horizontal scrolling at a minimum width of 360 px. | T0.5, T1.7 |
| D11 | **How do members identify each other?** D8 covers login only, but §7.8 and Screens 3, 6 and 8 show the assigned member. | Registration requires a display name, which is shown everywhere instead of the email. | T1.1, T2.4, T5.3, T6.1 |
| D12 | **How do registration and login behave in the details?** | Registering logs the user in. Login email is case-insensitive. A logged-in user opening login or registration is redirected to `/`. | T1.1 |
| D13 | **Where does a user with a household land?** | The final target of `/` is Screen 4, the Personal Chore Dashboard (§5 step 8). Until T5.2 exists, `/` shows a minimal page with the household name, including right after creating a household. | T1.4, T5.2 |
| D14 | **Can an email contain non-ASCII characters?** SQLite's `LOWER()` folds only ASCII, so the case rules in D8 and D12 couldn't hold for internationalised domains. | No. An email with any non-ASCII character is rejected, so people with internationalised-domain addresses can't register. Accepted emails contain only ASCII letters, which D8 and D12 cover. | T0.2, T1.1 |
| D15 | **What happens when a user who already has a household opens Screen 2?** | They are redirected to `/`, whatever `/` shows at the time (D13). | T1.4 |

## E0 — Foundation

### T0.1 Configure the project · P0 · S
- Add `templates/` to `TEMPLATES['DIRS']`, and set `STATICFILES_DIRS` and `STATIC_ROOT`.
- Read `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` and `DATABASE_URL` from the environment, and add `.env.example`.
- Make the documented `uv run` commands work from a local `.env` file, with nothing exported in the shell.
- Use `dj-database-url` to parse `DATABASE_URL`, falling back to the local SQLite file when it isn't set (D9).

**Done when:**
- [x] `config/settings.py` has no `SECRET_KEY` value or fallback, and no file git would commit, apart from this backlog, contains the text `django-insecure`. This must be true **before the first commit of `config/`**, because that file is currently untracked.
- [x] With `SECRET_KEY` unset and no `.env` file, `uv run python manage.py check` exits non-zero.
- [x] `.env.example` lists `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` and `DATABASE_URL` with placeholder values only. Git ignores `.env` and doesn't ignore `.env.example`.
- [x] After copying `.env.example` to `.env`, with nothing exported in the shell, `uv run python manage.py check` passes.
- [x] A variable set in the shell takes priority over the same variable in `.env`.
- [x] `DEBUG=True` gives `DEBUG` as `True` and `DEBUG=False` gives `False`. Two hosts in `ALLOWED_HOSTS`, in the format `.env.example` shows, give a list of both.
- [x] With `DATABASE_URL` unset or empty, the database is SQLite at `db.sqlite3` in the project root. With it set to another SQLite URL, the database is that file (D9).
- [x] `dj-database-url` is in `pyproject.toml`, and `uv lock --check` passes (D9).
- [x] `TEMPLATES['DIRS']` includes `templates/` and `STATICFILES_DIRS` includes `static/`. `manage.py collectstatic --noinput` writes to `STATIC_ROOT` and leaves `git status --short` unchanged.
- [x] `USE_TZ = True` and `TIME_ZONE = 'UTC'` are still set (§7.3).

### T0.2 Add a custom user model · P0 · S
Depends on: T0.1

- Create `accounts.User` from `AbstractUser`, with a unique email as the login field (D8).
- Set `AUTH_USER_MODEL`.

**Done when:**
- [x] `AUTH_USER_MODEL` is `accounts.User`, and `manage.py migrate` succeeds on an empty database.
- [x] `manage.py showmigrations --plan` lists `accounts.0001_initial` before `admin.0001_initial`, and no other project app has a migration yet. Swapping the user model later is difficult, so it has to happen first.
- [x] A user created with an email and password, and no username, can be authenticated with that email and password (D8).
- [x] `manage.py createsuperuser` asks for an email and doesn't ask for a username (D8).
- [x] The database rejects a second user whose email differs from an existing one only in the letter case of ASCII letters, using a case-insensitive unique constraint (D8). The constraint doesn't have to fold non-ASCII letters, because accepted emails can't contain them (D14).
- [x] An email with a non-ASCII character in the local part or the domain, such as `sam@éxample.com`, is rejected by the user manager's `create_user` and `create_superuser`, by model validation and by `manage.py createsuperuser`, and no user is created. An all-ASCII domain, such as `sam@xn--xample-9ua.com`, isn't rejected by this rule. A direct `User.objects.create()` isn't covered and no database-level rejection is required, because it skips validation and no user-facing route uses it (D14).
- [x] `manage.py createsuperuser` given an email that differs from an existing one only in the letter case of ASCII letters behaves as it does for an exact duplicate: it reports the email as taken and asks again, with no traceback and no user created.
- [x] An empty or whitespace-only email is rejected by the user manager's `create_user` and `create_superuser`, by model validation and by `manage.py createsuperuser`. A direct `User.objects.create()` isn't covered, because it skips validation and no user-facing route uses it.

### T0.3 Set up the test tools · P0 · S
Depends on: T0.1, T0.2

- Add `pytest`, `pytest-django` and `factory-boy` as uv dev dependencies.
- Add pytest settings to `pyproject.toml`, and shared factories to `tests/`.

**Done when:**
- [x] `pytest`, `pytest-django` and `factory-boy` are dev dependencies in `pyproject.toml`, and `uv lock --check` passes.
- [x] With `.env` copied from `.env.example`, `uv run pytest` with no extra arguments finds at least one test in `tests/`, runs it and exits 0.
- [x] A smoke test saves a user from a shared factory in `tests/` to the test database and reads it back. Calling the factory twice gives two users with different emails.

### T0.4 Set up code quality and CI · P1 · S
Depends on: T0.3

- Configure `ruff`.
- Add a GitHub Actions workflow that runs lint, `manage.py makemigrations --check` and pytest.

**Done when:**
- [ ] `ruff` is a dev dependency configured in `pyproject.toml`, `uv lock --check` passes, and `uv run ruff check .` exits 0.
- [ ] A workflow in `.github/workflows/` triggers on `pull_request` with no branch filter.
- [ ] The workflow installs from `uv.lock`, then runs `ruff check`, `manage.py makemigrations --check` and `pytest`. None of these steps uses `continue-on-error`, so a failure in any of them fails the run.
- [ ] The workflow defines the environment values it needs and uses no GitHub repository secrets. With only those values set and no `.env` file, its three commands exit 0 locally.
- [ ] In a throwaway copy of the repository outside the working tree, adding a model field without a migration makes the workflow's `makemigrations --check` command exit non-zero.

### T0.5 Build the base layout · P0 · S
Depends on: T0.1

- Create `base.html` with a navigation area, Django messages and a mobile-friendly stylesheet. T1.1 and T1.7 add the links, because the pages and user states they depend on don't exist yet.
- Add 403 and 404 pages.

**Done when:**
- [ ] A page that extends `base.html` shows a navigation area with the name "Household Chores Manager", includes a viewport meta tag and loads the project stylesheet from `static/`.
- [ ] A Django message set by a view appears on the next rendered page and not on the page after that.
- [ ] With `DEBUG=False`, a view that raises `PermissionDenied` returns status 403 with the custom 403 page, which extends `base.html`.
- [ ] With `DEBUG=False`, an unknown URL returns status 404 with the custom 404 page, which extends `base.html`.
- [ ] The custom 404 page has no horizontal scrolling at a width of 360 px (D10).

No screens exist yet, so test-only views can prove these criteria. To check the width by hand, use `DEBUG=False` and `runserver --insecure`, so that the 404 page appears with its stylesheet.

## E1 — Accounts and Households

### T1.1 Registration, login and logout · P0 · M
Depends on: T0.2, T0.5

- Build Screen 1 using Django's auth views and a registration form that asks for an email, a display name and a password (D11). Password reset and email verification aren't included, because §4 lists only registering and logging in, and the MVP sends no email (§8).
- Add `/` as the place users go after logging in. T1.4 adds what it does for logged-in users.
- Honour a safe `next` redirect, which the invitation flow needs (T2.3).

**Done when:**
- [ ] Registering with a valid email, display name and password creates one user with that display name and a hashed password. The form doesn't ask for a username (§4, D8, D11).
- [ ] A blank or whitespace-only display name is rejected with an error on the form, and no user is created (D11).
- [ ] A password that fails a configured validator, such as `12345678`, is rejected with an error on the form, and no user is created.
- [ ] A blank or malformed email is rejected with an error on the form, and no user is created.
- [ ] An email with a non-ASCII character in the local part or the domain, such as `sam@éxample.com`, is rejected with an error on the registration form, and no user is created (D14).
- [ ] An email that differs from an existing one only by letter case is rejected with an error on the form, and no second user is created (D8).
- [ ] Registering logs the new user in. With no `next`, it sends them to `/` (D12).
- [ ] Logging in with the correct email and password starts a session (§4, D8).
- [ ] Logging in with the registered email in different letter case, such as `Sam@Example.com` for `sam@example.com`, starts a session (D12).
- [ ] A logged-in user requesting the login or registration page is redirected to `/` (D12).
- [ ] A wrong password, an unknown email or an email with a non-ASCII character shows an error, and the user stays logged out (D14).
- [ ] A POST to logout ends the session. A GET to logout doesn't end it.
- [ ] Logging in with no `next` sends the user to `/`. A logged-out user requesting `/` is redirected to login, and a logged-in user requesting it gets a status below 400.
- [ ] A user who logs in or registers with an internal `next` arrives at that URL once logged in (T2.3).
- [ ] An external `next`, such as `https://evil.example/` or `//evil.example/`, is ignored on both login and registration.

### T1.2 Household and membership models · P0 · M
Depends on: T0.2

- `Household`: name, IANA `timezone`, `generation_time`.
- `Membership`: user, household, role, `is_active`, `joined_at`, `left_at`. Rows are deactivated and never deleted, so history and rotation references stay valid.
- Add database constraints as described below.

**Done when:**
- [ ] The database rejects a second active membership for a user, using a partial unique constraint (§7.1).
- [ ] The database rejects a second active admin in a household, using a partial unique constraint (§7.1).
- [ ] Inactive rows don't count towards either constraint. A user who has left can hold a new active membership, and a household whose former admin has an inactive row can have a new active admin (§7.5).
- [ ] Model validation accepts `America/New_York` and `America/Port-au-Prince`, and rejects a blank time zone and `Mars/Base` (§7.3).
- [ ] Model validation rejects a blank or whitespace-only household name, a missing `generation_time` and a role other than admin or member.
- [ ] `joined_at` is set when a membership is created, and `is_active` is true by default.
- [ ] Deleting a user or household that has a membership row fails, and the row stays, including when the membership is inactive (§7.8).

### T1.3 Household access control · P0 · S
Depends on: T1.2, T1.4

- Add `household_member_required` and `household_admin_required` helpers.
- Fetch data through the current user's household, never through a household ID from the URL.

**Done when:**
- [ ] A logged-out user requesting a view with either helper is redirected to login, with the requested path as `next`.
- [ ] A user with no household is redirected to Screen 2 by either helper. This includes a user whose only membership is inactive.
- [ ] A member gets status 200 from a member view and status 403 from an admin view, on both GET and POST (§3).
- [ ] An admin gets status 200 from both a member view and an admin view (§3).
- [ ] A member or admin requesting another household's record by its ID gets status 404, and the same request for a record in their own household succeeds (§11).
- [ ] A household ID in the URL, query string or POST data doesn't change which household the helpers provide (§11).

Few household screens exist yet, so test-only views can prove these criteria.

### T1.4 Create or Join screen · P0 · M
Depends on: T0.5, T1.1, T1.2

- Build Screen 2 with household name, time zone and generation time. T2.3 adds the option to join with an invitation link.
- Creating a household also makes the creator its admin, in a single transaction.
- Until T5.2 exists, make `/` show a minimal page with the household name to a user with a household (D13).

**Done when:**
- [ ] A logged-out user requesting Screen 2 is redirected to login, with Screen 2 as `next`.
- [ ] A logged-in user with no household who requests `/` is redirected to Screen 2.
- [ ] A member or admin requesting `/` gets status 200 and a page in the base layout that shows their household's name (D13).
- [ ] Submitting a valid form creates one household with the submitted values, and one active membership making the creator its admin (§3, §7.1). The creator is then redirected to `/` and sees the new household's name (D13).
- [ ] If creating the membership fails, no household is saved, so no household exists without an active admin (§7.1).
- [ ] A user with an active membership who opens Screen 2 is redirected to `/` (D15).
- [ ] A POST from a user who already has an active membership, including a double submission, creates no household or membership and changes nothing (§7.1).
- [ ] A user whose only membership is inactive can create a household (§7.5).
- [ ] The time zone field offers a list of valid IANA names that includes `America/New_York` and `America/Port-au-Prince` (§7.3).
- [ ] A POST with a time zone outside that list, such as `Mars/Base`, shows an error and creates nothing (§7.3).
- [ ] A blank or whitespace-only name, or a missing or invalid generation time, such as `25:00`, shows an error and creates nothing.

### T1.5 Show times in the household's time zone · P0 · S
Depends on: T1.2

- Add middleware that activates the current household's time zone for each request.

**Done when:**
- [ ] For a member of an `America/New_York` household, a stored `2026-01-15 12:00 UTC` displays as 07:00 and a stored `2026-07-15 12:00 UTC` displays as 08:00, and both values stay in UTC in the database (§7.3).
- [ ] A logged-out user, a user with no household and a user whose only membership is inactive see that same value in UTC.
- [ ] A household's time zone doesn't carry over: a logged-out request straight after a member's request displays times in UTC.
- [ ] After a household's time zone changes, its members' next request uses the new time zone.

No screen displays a timestamp yet, so a test-only view can prove these criteria.

### T1.6 Household Settings screen · P0 · S
Depends on: T0.5, T1.3, T1.5

- Build Screen 7, where the admin edits the name, time zone and generation time.

**Done when:**
- [ ] The admin sees the household's current name, time zone and generation time in the form (§7.2).
- [ ] Saving valid changes stores all three values on the admin's own household and shows a success message. Other households don't change (§7.2, §11).
- [ ] A logged-out user is redirected to login, and a user with no household is redirected to Screen 2.
- [ ] A member gets status 403 on both GET and POST, and a member's POST changes nothing (§3).
- [ ] An invalid time zone, a blank or whitespace-only name, or a missing or invalid generation time shows an error and saves nothing (§7.3).
- [ ] Changing only the time zone leaves the generation time's clock value unchanged, because it means local time in the new zone (§7.2, §7.3).
- [ ] Saving updates only these three fields and doesn't start assignment generation (D4). T4.3 proves that no second run happens.

### T1.7 Navigation for each user state · P0 · S
Depends on: T1.1, T1.4, T1.6

- Add the navigation links for each user state to `base.html`.
- Each screen task from E2 onward adds its own link, as these criteria only cover the screens M2 delivers.

**Done when:**
- [ ] Logged-out users see the login and registration links, and no other links.
- [ ] Logged-in users with no household, including those whose only membership is inactive, see the Create or Join link and the logout control.
- [ ] Members see the logout control, and no Create or Join or Household Settings link.
- [ ] Admins see the Household Settings link and the logout control, and no Create or Join link.
- [ ] The logout control sends a POST (T1.1).
- [ ] Every link above returns status 200 for the user who sees it.
- [ ] At a width of 360 px, Screens 1, 2 and 7 and the `/` page have no horizontal scrolling, with the navigation for each user state that can open them (D10).

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
- [ ] After today's run, changing the household's generation time or time zone creates no second run for that local date, and the new settings apply from the next one (D4).

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
- Make this screen the target of `/`, replacing the minimal page from T1.4 (D13).

**Done when:**
- [ ] A member or admin requesting `/` reaches this screen, and the minimal page from T1.4 is gone (§5 step 8, D13).
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
- [ ] The email letter-case tests for T0.2 and T1.1 run on PostgreSQL, and the verification report states the database locale they ran under, because case folding can depend on it.

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
| **M2 Household** | T1.1, T1.2, T1.4, T1.3, T1.5, T1.6, T1.7 | Register, create a household and change its settings |
| **M3 Membership** | T2.1–T2.4, T2.6 | Invite someone, have them join and transfer the admin role |
| **M4 Chores** | T3.1–T3.3 | The admin manages the chore list |
| **M5 Rotation** | T4.1–T4.5, T2.5, T4.6 | The command generates fair assignments |
| **M6 Daily use** | T5.1–T5.3 | Members see and complete their chores |
| **M7 Feedback** | T6.1–T6.4 | History and notifications work |
| **M8 Release** | T8.1, T7.1, T7.2, T8.2, T8.3, T7.3, T8.4 | The deployed app passes the §11 check |

T2.5 moves to M5 because cancelling assignments needs the `Assignment` model from T4.1. T1.4 comes before T1.3 because the helpers redirect users with no household to Screen 2.

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
