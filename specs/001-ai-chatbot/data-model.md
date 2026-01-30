# Data Model: AI Chatbot

**Feature**: `001-ai-chatbot` | **Date**: 2026-01-30

## Entity Relationship Diagram

```
User (Better Auth, existing)
  │
  ├── 1:N → Task (existing, unchanged)
  │         id, user_id, title, description, completed, created_at, updated_at
  │
  └── 1:N → ChatMessage (NEW)
            id, user_id, role, content, created_at
```

## Entities

### ChatMessage (NEW — application managed, snake_case)

Stores individual chat messages for history persistence.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | integer | PK, auto-increment | Unique message identifier |
| user_id | string | FK → User.id, indexed | Owner of the message |
| role | string | "user" or "assistant" | Who sent the message |
| content | text | max 5000 chars | Message content |
| created_at | datetime | UTC, auto-set | When the message was sent |

**Validation Rules**:
- `role` must be one of: "user", "assistant"
- `content` must not be empty
- `content` max length: 5000 characters (2000 for user input, 5000 to accommodate AI responses)
- `user_id` must reference an existing authenticated user

**Indexes**:
- `user_id` — for fetching user's chat history
- `(user_id, created_at)` — for ordered history queries

### Task (EXISTING — unchanged)

No changes to the existing Task entity. The chat feature reads and modifies tasks through the same SQLModel operations used by the REST API.

| Field | Type | Constraints |
|-------|------|-------------|
| id | integer | PK, auto-increment |
| user_id | string | indexed |
| title | string | required |
| description | string | default "" |
| completed | boolean | default false |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |

## Request/Response Schemas (not persisted)

### ChatRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | string | yes | User's natural language message (max 2000 chars) |

### ChatResponse

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reply | string | yes | AI assistant's text response |
| action_taken | string | no | Description of task action performed (e.g., "created_task", "completed_task") |
| task_data | object | no | Affected task details (Task JSON) |

## State Transitions

### Chat Message Flow
```
User types message
  → ChatMessage(role="user") saved
  → AI processes with tools
  → ChatMessage(role="assistant") saved
  → Response returned to frontend
```

### Tool Execution Flow
```
AI decides to call tool
  → Tool executed against Task table
  → Tool result returned to AI
  → AI generates human-friendly response
  → Response includes action_taken + task_data
```
