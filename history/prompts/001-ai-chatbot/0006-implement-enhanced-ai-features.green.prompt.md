---
id: "0006"
title: Implement Enhanced TaskFlow AI Features
stage: green
date: 2026-01-30
surface: agent
model: claude-opus-4-5-20251101
feature: 001-ai-chatbot
branch: 001-ai-chatbot
user: nm
command: implement
labels: ["ai-tools", "priority", "due-date", "search", "filter", "bulk-ops"]
links:
  spec: specs/001-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/models.py
  - backend/app/schemas.py
  - backend/app/routes/tasks.py
  - backend/app/chat_tools.py
  - backend/app/routes/chat.py
  - frontend/src/types/task.ts
  - frontend/src/lib/api.ts
  - frontend/src/app/dashboard/page.tsx
tests: []
---

## Prompt

Implement the following plan:

# Plan: Enhanced TaskFlow AI Features

## Summary

Add priority, due dates, and 4 new AI chat tools to TaskFlow. Upgrade from 5 to 9 AI tools.

## New AI Capabilities

| Tool | Description |
|------|-------------|
| `create_task` | **Updated** - now accepts `priority` and `due_date` |
| `update_task` | **Updated** - now accepts `priority` and `due_date` |
| `search_tasks` | **New** - search by keyword in title/description |
| `filter_tasks` | **New** - filter by status, priority, or due window (overdue/today/this_week) |
| `complete_all_tasks` | **New** - mark all incomplete tasks as done |
| `delete_completed_tasks` | **New** - bulk delete all completed tasks |

## New Task Fields

- `priority`: string ("low", "medium", "high", "urgent"), default "medium"
- `due_date`: optional datetime, nullable

## Implementation Steps

1. Backend model + DB migration
2. Backend schemas
3. Backend REST routes
4. Chat tools - update existing + add new
5. Enhanced system prompt
6. Frontend types + display

## Response

Implemented all 6 steps of the enhanced AI features plan:

1. **Backend model** (`models.py`): Added `priority` (str, default "medium") and `due_date` (Optional[datetime]) fields to Task model.
2. **Backend schemas** (`schemas.py`): Added `priority` and `due_date` to `TaskCreate` and `TaskUpdate` Pydantic models.
3. **Backend REST routes** (`routes/tasks.py`): Updated `create_task` handler to pass `priority` and `due_date` to the Task constructor.
4. **Chat tools** (`chat_tools.py`): Updated `create_task` and `update_task` tool schemas and handlers to support priority/due_date. Added 4 new tools: `search_tasks`, `filter_tasks`, `complete_all_tasks`, `delete_completed_tasks`. Updated `_task_to_dict` and `list_tasks` to include new fields. Added `_parse_due_date` helper for ISO date parsing. Total tools: 9.
5. **System prompt** (`routes/chat.py`): Enhanced `_build_system_prompt` to show priority and due date per task, overdue/due-today counts, and list all new capabilities.
6. **Frontend** (`types/task.ts`, `api.ts`, `dashboard/page.tsx`): Added `priority` and `due_date` to Task interface. Updated API method signatures. Added priority badges (colored by level) and due date display (with overdue/today coloring) on task cards.
7. **DB migration**: Ran `ALTER TABLE tasks ADD COLUMN` for `priority` (VARCHAR, default 'medium') and `due_date` (TIMESTAMP WITH TIME ZONE) on the Neon PostgreSQL database.

All TypeScript and Python imports verified clean. 9 tools loaded successfully.
