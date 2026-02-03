---
id: "0008"
title: E2E Testing and Runtime Bugfixes
stage: green
date: 2026-01-31
surface: agent
model: claude-opus-4-5-20251101
feature: 001-ai-chatbot
branch: 001-ai-chatbot
user: nm
command: implement
labels: ["e2e-testing", "bugfix", "migration", "groq-compat"]
links:
  spec: specs/001-ai-chatbot/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - backend/app/db.py
  - backend/app/chat_tools.py
tests:
  - "T01: Health endpoint - PASS"
  - "T02: Authenticated task listing - PASS"
  - "T03: Unauthenticated access denied (401) - PASS"
  - "T04: Cross-user access denied (403) - PASS"
  - "T05: Create task via REST - PASS"
  - "T06: Toggle task complete - PASS"
  - "T07: Update task - PASS"
  - "T08: Delete task - PASS"
  - "T09: Message >2000 chars rejected (422) - PASS"
  - "T10: Chat creates new session - PASS"
  - "T11: task_data in response - PASS"
  - "T12: Send in same session - PASS"
  - "T13: List sessions - PASS"
  - "T14: Get session messages - PASS"
  - "T15: task_data persisted in DB messages - PASS"
  - "T16: Complete task via chat - PASS"
  - "T17: Delete task via chat - PASS"
  - "T18: Legacy chat history endpoint - PASS"
  - "T19: New chat (null session_id) - PASS"
  - "T20: Delete session - PASS"
  - "T21: Deleted session returns 404 - PASS"
---

## Prompt

Run frontend and backend application and check all functions work properly as developer.

## Response snapshot

Started both servers and ran 21 E2E tests covering all Phase 3 features. Found and fixed 3 runtime bugs:

1. **db.py migration used SQLite PRAGMA on PostgreSQL** - Changed `PRAGMA table_info()` to `information_schema.columns` query for PostgreSQL compatibility.

2. **chat_tools.py task_id type mismatch** - Groq LLM returns `task_id` as string instead of integer, causing API validation failure. Fixed by accepting `["integer", "string"]` in tool schemas and adding int coercion in `execute_tool()`.

3. **chat_tools.py arguments=None crash** - When LLM generates empty arguments, `json.loads` returns None causing `TypeError` on `"task_id" in arguments`. Added `if not arguments: arguments = {}` guard.

All 21 tests pass: health, auth (401/403), task CRUD (create/toggle/update/delete), chat sessions (create/list/messages/delete), AI chat (create/complete/delete tasks via NL), message validation, task_data persistence, session continuity.

## Outcome

- Impact: 3 runtime bugs fixed, 21/21 E2E tests pass
- Tests: 21 E2E curl tests covering all Phase 3 features
- Files: 2 modified (db.py, chat_tools.py)
- Next prompts: Fix better-auth JWKS EdDSA key storage format for new user signup
- Reflection: PostgreSQL vs SQLite assumptions caught by live testing; LLM type coercion is a common production issue

## Evaluation notes (flywheel)

- Failure modes observed: SQLite PRAGMA on PostgreSQL, LLM string-vs-int tool args, None arguments
- Graders run and results (PASS/FAIL): 21/21 PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add integration test suite as automated script
