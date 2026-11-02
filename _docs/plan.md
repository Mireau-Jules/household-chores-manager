# Household Chores Manager — MVP Scope

## 1. Product Overview

A web application that helps people living together coordinate household responsibilities through automatically generated daily chore assignments, fair rotation, and individual task tracking.

## 2. Target Audience

**Shared households:** Any group of people living together, regardless of their relationship.

## 3. User Roles

| Role | Responsibilities |
|---|---|
| Administrator | Creates the household, invites members, manages chores and configures household settings. |
| Member | Views personal chore assignments and marks chores as completed. |

## 4. Core MVP Features

| Feature | Description |
|---|---|
| Authentication | Users can register and log in. |
| Household Management | Users can create and manage a household. |
| Invitations | Administrators can generate shareable invitation links. |
| Member Management | Administrators can manage household members. |
| Chore Management | Administrators can create, edit and delete daily chores. |
| Automatic Rotation | The system rotates chores among household members every day. |
| Daily Scheduling | Administrators configure the time when new assignments are generated. |
| Personal Dashboard | Members see their own assigned chores. |
| Task Tracking | Members can mark assigned chores as completed. |
| Pending Tasks | Incomplete chores remain pending. |
| Activity History | All household members can view completed chores. |
| Notifications | Support for in-app notifications. |

## 5. Main Application Workflow

1. A user registers or logs in.
2. The user creates a household or joins one through an invitation link.
3. The household administrator invites other members.
4. The administrator creates the household's daily chores.
5. The administrator configures the chore rotation and daily generation time.
6. The system automatically generates daily assignments.
7. Members access their personal dashboards.
8. Members complete their assigned chores and mark them as completed.
9. The system updates chore statuses and the household activity history.

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

## 7. Business Rules

- Each household has its own members and chores.
- Each household has one administrator.
- Daily assignments are generated at the administrator's configured time.
- Chores rotate among household members every day.
- A completed chore cannot be marked as completed twice.
- Incomplete chores remain pending.
- Members can view their personal assignments.
- All members can access the household completion history.
- New members must be incorporated into the chore rotation.
- The system must prevent duplicate assignment generation for the same household and date.

## 8. Features Outside the MVP Scope

- Gamification and reward points.
- Household expense management.
- Chat and messaging.
- AI-powered chore recommendations.
- Photo verification.
- Advanced analytics.
- Automatic reassignment of incomplete chores.

## 9. Suggested Technical Architecture

| Layer | Technology |
|---|---|
| Framework | Python + Django (managed with `uv`) |
| Frontend | Django Templates + HTML/CSS |
| Database | SQLite (Development) / PostgreSQL (Production) |
| Authentication | Django Built-in Auth |
| Testing | `pytest` / Django Test Runner |

## 10. MVP Development Phases

1. Authentication and household creation.
2. Invitations and member management.
3. Chore creation and configuration.
4. Daily chore rotation algorithm.
5. Personal dashboard and completion tracking.
6. Activity history.
7. Testing and verification.
