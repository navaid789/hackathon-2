# Data Model: Kafka + Dapr Cloud Deployment

**Branch**: `003-kafka-dapr-cloud` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)

## Overview

Phase 5 introduces 4 new database entities (stored in the existing Neon PostgreSQL) and 1 event schema (transmitted via Kafka). No changes to existing entities (Task, ChatSession, ChatMessage).

---

## New Database Entities

### 1. TaskEvent (event log table)

Stores a local copy of published events for debugging, replay, and idempotency tracking.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | TEXT | PRIMARY KEY | Unique event ID (UUID v4) |
| event_type | TEXT | NOT NULL | `task.created`, `task.updated`, `task.completed`, `task.deleted` |
| user_id | TEXT | NOT NULL, INDEX | User who triggered the event |
| task_id | INTEGER | NOT NULL | Related task ID |
| payload | TEXT (JSON) | NOT NULL | Full event data as JSON |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | When the event was created |
| published | BOOLEAN | NOT NULL, DEFAULT false | Whether successfully published to Kafka |

**Relationships**: References `user_id` from the `user` table (better-auth). References `task_id` from the `tasks` table (may be null if task was deleted).

**State Transitions**: `published: false` → `published: true` (after successful Dapr publish call).

---

### 2. Notification

Stores generated notifications for users (overdue alerts, daily summaries).

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO | Unique notification ID |
| user_id | TEXT | NOT NULL, INDEX | Target user |
| notification_type | TEXT | NOT NULL | `overdue_alert`, `daily_summary` |
| title | TEXT | NOT NULL | Short notification title |
| content | TEXT | NOT NULL | Notification body (may be JSON for summaries) |
| related_task_id | INTEGER | NULL | Related task ID (for overdue alerts) |
| is_read | BOOLEAN | NOT NULL, DEFAULT false | Whether user has seen this |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | When generated |

**Relationships**: References `user_id` from `user` table. Optionally references `task_id` from `tasks` table.

**State Transitions**: `is_read: false` → `is_read: true` (when user reads notification via API).

---

### 3. AnalyticsBucket

Stores per-user, per-day aggregated analytics data. Updated incrementally by the worker as events are consumed.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| id | INTEGER | PRIMARY KEY, AUTO | Row ID |
| user_id | TEXT | NOT NULL | User this bucket belongs to |
| bucket_date | DATE | NOT NULL | The day this bucket covers |
| tasks_created | INTEGER | NOT NULL, DEFAULT 0 | Tasks created on this day |
| tasks_completed | INTEGER | NOT NULL, DEFAULT 0 | Tasks completed on this day |
| tasks_deleted | INTEGER | NOT NULL, DEFAULT 0 | Tasks deleted on this day |
| total_completion_time_hours | FLOAT | NOT NULL, DEFAULT 0.0 | Sum of time-to-complete for completed tasks (hours) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Row creation time |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update time |

**Unique Constraint**: `(user_id, bucket_date)` — one row per user per day.

**Relationships**: References `user_id` from `user` table.

**Usage**: Analytics API queries this table to compute: total created, total completed, completion rate, average time-to-complete, and daily trends for a time window.

---

### 4. ProcessedEvent

Deduplication table for idempotent event processing.

| Field | Type | Constraints | Description |
|-------|------|------------|-------------|
| event_id | TEXT | PRIMARY KEY | Event ID from CloudEvents envelope |
| processed_at | TIMESTAMP | NOT NULL, DEFAULT now() | When this event was processed |

**Purpose**: Before processing an event, the worker checks if `event_id` exists in this table. If yes, skip (already processed). If no, process and insert. This ensures exactly-once semantics despite at-least-once delivery.

---

## Event Schema (Kafka / CloudEvents)

Events are transmitted via Kafka, wrapped in CloudEvents 1.0 format by Dapr automatically. The application provides the `type` and `data` fields.

### Base Envelope (added by Dapr)

| Field | Type | Description |
|-------|------|-------------|
| specversion | string | Always "1.0" |
| type | string | Event type (e.g., "task.created") |
| source | string | "/taskflow/backend" |
| id | string | Unique event UUID |
| time | string (ISO 8601) | Event timestamp |
| datacontenttype | string | "application/json" |
| data | object | Event-specific payload |

### Event Type: `task.created`

```json
{
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "title": "Buy groceries",
    "description": "",
    "priority": "medium",
    "due_date": "2026-02-10T00:00:00Z",
    "created_at": "2026-02-06T10:30:00Z"
  }
}
```

### Event Type: `task.updated`

```json
{
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "changes": {
      "priority": {"old": "medium", "new": "high"},
      "title": {"old": "Buy groceries", "new": "Buy organic groceries"}
    },
    "updated_at": "2026-02-06T11:00:00Z"
  }
}
```

### Event Type: `task.completed`

```json
{
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "completed": true,
    "completed_at": "2026-02-07T14:00:00Z",
    "time_to_complete_hours": 27.5
  }
}
```

### Event Type: `task.deleted`

```json
{
  "data": {
    "task_id": 42,
    "user_id": "user-abc-123",
    "title": "Buy groceries",
    "deleted_at": "2026-02-08T09:00:00Z"
  }
}
```

---

## Existing Entities (No Changes)

These entities from previous phases remain unchanged:

- **Task** (`tasks` table): id, user_id, title, description, completed, priority, due_date, created_at, updated_at
- **ChatSession** (`chat_sessions` table): id, user_id, title, created_at, updated_at
- **ChatMessage** (`chat_messages` table): id, user_id, role, content, session_id, task_data, action_taken, created_at
- **User** (`user` table, managed by better-auth): id, name, email, etc.
