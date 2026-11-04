# Household Chores Manager — MVP Scope

## 1. Product Overview

A web application that helps people living together coordinate household responsibilities through automatically generated daily chore assignments, fair rotation, and individual task tracking.

The primary objective is to improve household coordination by making daily responsibilities clear and ensuring that chores are distributed fairly among members.

## 2. Target Audience

**Shared households:** Any group of people living together, regardless of their relationship.

Examples include:
- Families
- Roommates
- Students sharing accommodation
- Couples
- Other shared living arrangements

## 3. User Roles

| Role | Responsibilities |
|---|---|
| Administrator | Creates the household, invites members, manages chores, configures settings and manages membership. |
| Member | Views personal chore assignments, completes chores and accesses household activity history. |

**Important:** The administrator is also a household member and participates in the daily chore rotation.

## 4. Core MVP Features

| Feature | Description |
|---|---|
| Authentication | Users can register and log in. |
| Household Management | Users can create and manage a household. |
| Invitations | Administrators can generate shareable invitation links. |
| Member Management | Administrators can manage household members and transfer administration. |
| Chore Management | Administrators can create, edit and delete daily chores. |
| Automatic Rotation | The system distributes and rotates chores among active household members every day. |
| Daily Scheduling | Administrators configure the time when new assignments are generated. |
| Time Zone Management | Each household has its own time zone. |
| Personal Dashboard | Members see their own assigned chores. |
| Task Tracking | Members can mark assigned chores as completed. |
| Pending Tasks | Incomplete chores remain pending and retain their original assignee. |
| Activity History | All household members can view completed chores. |
| In-App Notifications | Members receive notifications about new assignments and pending chores. |

## 5. Main Application Workflow

1. A user registers or logs in.
2. The user creates a household or joins one through an invitation link.
3. The household administrator invites other members.
4. The administrator creates the household's daily chores.
5. The administrator configures the chore rotation, time zone and daily generation time.
6. A scheduled background process checks which households are due for new assignments.
7. The system generates daily assignments automatically.
8. Members access their personal dashboards.
9. Members complete their assigned chores and mark them as completed.
10. The system updates chore statuses and the household activity history.
11. Members receive relevant in-app notifications.

## 6. Main Application Screens

The MVP will include the following eight screens:

1. Login / Registration
2. Create or Join Household
3. Household Dashboard
4. Personal Chore Dashboard
5. Chore Management
6. Member Management
7. Household Settings
8. Activity History

## 7. Business Rules and Design Decisions

### 7.1 Household Management

- Each household has its own members and chores.
- Each household has exactly one administrator.
- A user can belong to only one household in the MVP.
- The administrator is included in the chore rotation.
- The administrator can transfer administrative privileges to another active member.
- An administrator cannot leave a household without first transferring the administrator role.
- Only active household members participate in chore rotation.

### 7.2 Daily Scheduling

- Each household has a configurable daily assignment generation time.
- Each household has its own time zone.
- The administrator selects the time zone during household creation or updates it through household settings.
- A scheduled process checks for households whose generation time has arrived.
- The scheduler runs every five minutes using a cron job and a Django management command.
- The system generates assignments according to each household's local date and time.
- The system must prevent duplicate assignment generation for the same household and local date.

**Scheduler implementation:**

Use a Django management command executed periodically by the hosting platform's cron service.

Celery and Redis are not required for the MVP.

### 7.3 Time Zone Management

- Each household stores its own IANA time zone identifier (for example, `America/Port-au-Prince` or `America/New_York`).
- All scheduling decisions use the household's local time.
- Assignment dates are based on the household's local calendar date, not the server's date.
- Database timestamps are stored in UTC.
- Django's time zone support must be enabled.

### 7.4 Chore Management

- Only the administrator can create, edit and delete daily chores.
- All chores are recurring daily chores.
- Each chore represents one task that must be assigned every day.
- Weekly, monthly and one-time chores are outside the MVP scope.
- Each active chore receives one assignment per household day.

### 7.5 Automatic Rotation and Fairness

The system uses a round-robin rotation algorithm.

The following rules apply:

- Each daily chore is assigned to one active household member.
- Each chore maintains its own rotation position.
- The administrator participates in the rotation.
- The system distributes assignments as evenly as possible when there are more chores than members.
- When there are fewer chores than members, the rotation continues across days so that different members receive assignments over time.
- The system stores the last assigned member or rotation position for each chore.
- The rotation position must be preserved when a new member joins.
- When a member leaves, the rotation continues using the remaining active members.
- The system must not assign new chores to inactive members.

**Membership changes:**

- New members join the rotation at the next assignment generation.
- Existing rotation positions are preserved.
- Departing members' completed assignments remain in the activity history.
- Their incomplete assignments are marked as cancelled when they leave.
- Cancelled assignments are not automatically reassigned.

### 7.6 Pending Chores

- Incomplete chores remain pending.
- Pending chores retain their original assignee.
- The next day's generation does not cancel or replace previous pending assignments.
- New daily assignments are generated independently.
- Multiple pending assignments may exist for the same recurring chore across different days.
- No automatic reassignment is performed.

### 7.7 Task Completion

- Members can mark their own assigned chores as completed.
- A completed assignment cannot be marked as completed twice.
- Each completion records its completion timestamp.
- Members cannot modify another member's assignment.
- The administrator cannot mark a member's chore as completed on their behalf.

### 7.8 Activity History

- All active household members can view the household's completion history.
- The history displays the chore name, assigned member, assignment date and completion date.
- Cancelled assignments are distinguishable from completed assignments.
- Historical records are preserved when members leave the household.

### 7.9 Notifications

The MVP supports in-app notifications only.

The following events trigger notifications:

1. **New assignments:** Members receive a notification when their daily chores are generated.
2. **Pending chores:** Members receive a reminder about incomplete assignments.

Email and push notifications are postponed to future versions.

### 7.10 Invitation Links

- Only the administrator can generate invitation links.
- Invitation links expire after seven days.
- Each invitation link can be used only once.
- A link becomes invalid after successful acceptance.
- Expired or already-used links cannot be accepted.
- A user who already belongs to another household cannot join a second household.

## 8. Features Outside the MVP Scope

The following features will be considered for future versions:

- Gamification and reward points.
- Household expense management.
- Chat and messaging.
- AI-powered chore recommendations.
- Photo verification.
- Advanced analytics.
- Automatic reassignment of incomplete chores.
- Weekly, monthly and one-time chores.
- Email notifications.
- Push notifications.
- Multiple household membership.
- Mobile applications.

## 9. Technical Architecture

| Layer | Technology |
|---|---|
| Programming Language | Python |
| Framework | Django |
| Package Management | uv |
| Frontend | Django Templates + HTML/CSS |
| Database (Development) | SQLite |
| Database (Production) | PostgreSQL |
| Authentication | Django Built-in Authentication |
| Scheduling | Cron + Django Management Command |
| Testing | pytest / Django Test Runner |
| Version Control | Git + GitHub |

### Suggested Project Structure

```text
household-chores/
│
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── accounts/
│   ├── households/
│   ├── chores/
│   ├── assignments/
│   └── notifications/
│
├── templates/
├── static/
│
├── tests/
├── requirements/
│
├── manage.py
├── pyproject.toml
├── uv.lock
└── README.md
```

## 10. MVP Development Phases

### Phase 1: Authentication and Household Management
- User registration and login.
- Household creation.
- Household administrator role.
- Household time zone configuration.
- Household membership rules.

### Phase 2: Invitations and Member Management
- Invitation link generation.
- Invitation expiration and validation.
- Joining a household.
- Member management.
- Administrator transfer.

### Phase 3: Chore Management
- Create daily chores.
- Edit and delete chores.
- Display the household's chore list.
- Validate chore information.

### Phase 4: Daily Rotation Algorithm
- Implement round-robin assignment.
- Store rotation positions.
- Handle different numbers of chores and members.
- Handle membership changes.
- Implement the scheduled Django management command.
- Prevent duplicate daily assignments.
- Respect household time zones.

### Phase 5: Personal Dashboard and Task Tracking
- Display personal daily assignments.
- Mark chores as completed.
- Display pending assignments.
- Preserve previous assignments.

### Phase 6: Activity History and Notifications
- Household completion history.
- Assignment notifications.
- Pending chore reminders.
- Notification status tracking.

### Phase 7: Testing and Verification
- Authentication tests.
- Household permission tests.
- Invitation tests.
- Rotation fairness tests.
- Time zone and scheduling tests.
- Duplicate assignment prevention tests.
- Task completion tests.
- End-to-end workflow testing.

## 11. MVP Success Criteria

The MVP will be considered functional when:

- A user can register and log in.
- A user can create a household.
- An administrator can invite other members.
- An invitation link expires after seven days and cannot be reused.
- The administrator can create and manage daily chores.
- The administrator can configure the household's time zone and assignment generation time.
- The system generates assignments automatically.
- The rotation algorithm distributes chores fairly.
- The administrator participates in the rotation.
- New members are incorporated into the rotation.
- Members can view their individual assignments.
- Members can mark chores as completed.
- Incomplete chores remain pending with their original assignees.
- All members can view the household's activity history.
- In-app notifications are generated for new assignments and pending chores.
- Duplicate assignments are prevented.
- Household data and permissions remain isolated between users.

## 12. Final Product Goal

Build a simple, reliable household chore management application that improves coordination, distributes daily responsibilities fairly and gives every household member a clear understanding of their responsibilities.

**MVP Development Principle:** Prioritize simplicity, reliability and a well-defined chore rotation system. Avoid unnecessary complexity until the core household management workflow works correctly.