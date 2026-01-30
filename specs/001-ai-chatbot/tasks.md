# Tasks: AI Chatbot with Natural Language Task Management

**Input**: Design documents from `/specs/001-ai-chatbot/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/openapi.yaml, quickstart.md

**Tests**: Not explicitly requested. Tests omitted — E2E validation included in Polish phase.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and configure environment for AI chatbot feature

- [x] T001 Add `openai` and `groq` packages to `backend/requirements.txt`
- [x] T002 Install new Python dependencies in venv (`pip install openai groq`)
- [x] T003 Add `OPENAI_API_KEY`, `GROQ_API_KEY`, and `AI_PROVIDER` to `backend/.env`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core AI provider abstraction and tool definitions that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Create AI provider abstraction with OpenAI implementation in `backend/app/ai_provider.py` — Protocol class with `chat(messages, tools)` method, OpenAIProvider using `gpt-4o-mini`, `get_provider()` factory reading `AI_PROVIDER` env var
- [x] T005 [P] Create function-calling tool definitions in `backend/app/chat_tools.py` — 5 tools (`create_task`, `list_tasks`, `complete_task`, `delete_task`, `update_task`) as OpenAI-compatible JSON schemas with strict mode, plus `execute_tool()` function that runs tool calls against the DB
- [x] T006 [P] Add `ChatMessage` SQLModel to `backend/app/models.py` — fields: id (PK), user_id (str, indexed), role (str: user/assistant), content (text), created_at (datetime UTC)
- [x] T007 [P] Add `ChatRequest` and `ChatResponse` Pydantic schemas to `backend/app/schemas.py` — ChatRequest: message (str, max 2000), ChatResponse: reply (str), action_taken (Optional[str]), task_data (Optional[dict])
- [x] T008 [P] Create chat TypeScript types in `frontend/src/types/chat.ts` — ChatMessage interface (id, user_id, role, content, created_at), ChatResponse interface (reply, action_taken, task_data)

**Checkpoint**: Foundation ready — AI provider, tools, models, and schemas all defined. User story implementation can now begin.

---

## Phase 3: User Story 1 — Chat with Tasks via Natural Language (Priority: P1) MVP

**Goal**: Users can create, list, complete, delete, and update tasks by typing natural language messages. The backend interprets intent via AI function calling and executes task operations.

**Independent Test**: Send "Add a task to buy groceries" via POST `/api/{user_id}/chat` and verify a task is created and a confirmation reply is returned.

### Implementation for User Story 1

- [x] T009 [US1] Create chat route in `backend/app/routes/chat.py` — POST `/{user_id}/chat` endpoint: verify JWT, fetch user's tasks from DB, build system prompt with task context, call AI provider with tools, execute tool calls in a loop (max 5 iterations), save user+assistant messages to DB, return ChatResponse with reply/action_taken/task_data
- [x] T010 [US1] Register chat router in `backend/app/main.py` — import and include `chat_router` with prefix `/api`
- [x] T011 [US1] Add `sendMessage(userId, token, message)` method to `frontend/src/lib/api.ts` — POST to `/api/{userId}/chat` with `{ message }` body, returns ChatResponse

**Checkpoint**: At this point, the backend chat endpoint works end-to-end. A curl request can create/list/complete/delete tasks via natural language. Frontend can call the endpoint programmatically.

---

## Phase 4: User Story 2 — Conversational Chat Interface (Priority: P1)

**Goal**: A chat side panel on the dashboard where users type messages and see responses in a familiar messaging format with typing indicator and auto-scroll.

**Independent Test**: Open the dashboard, see the chat panel, type "Show my tasks", and see the response rendered as a chat bubble.

### Implementation for User Story 2

- [x] T012 [US2] Create `ChatPanel` component in `frontend/src/components/ChatPanel.tsx` — side panel with: message list (user/assistant bubbles with different styling), text input with Send button, typing/loading indicator while waiting for response, auto-scroll to latest message, responsive layout (side panel on desktop, full-width overlay on mobile)
- [x] T013 [US2] Integrate `ChatPanel` into dashboard in `frontend/src/app/dashboard/page.tsx` — add ChatPanel alongside task list, pass session/token/userId props, refresh task list when chat response includes `action_taken`, adjust layout to accommodate side panel (flex row on desktop)

**Checkpoint**: Users can manage tasks via the chat panel on the dashboard. Task list refreshes when chat actions modify tasks.

---

## Phase 5: User Story 3 — Smart Task Queries (Priority: P2)

**Goal**: Users can ask questions about their tasks ("How many tasks left?", "What did I finish today?") and get accurate, contextual answers.

**Independent Test**: Create 5 tasks (3 incomplete, 2 complete), ask "How many tasks are incomplete?" and verify the response says 3.

### Implementation for User Story 3

- [x] T014 [US3] Enhance system prompt in `backend/app/routes/chat.py` — include task count summary (total, completed, incomplete) and today's completed tasks in the system prompt context so the AI can answer aggregate queries accurately
- [x] T015 [US3] Add `list_tasks` tool response formatting in `backend/app/chat_tools.py` — ensure list_tasks returns structured data including completion dates so the AI can filter by "today", "this week", etc.

**Checkpoint**: The chatbot can answer questions about task counts, completion status, and temporal queries.

---

## Phase 6: User Story 4 — Chat History Persistence (Priority: P3)

**Goal**: Chat messages are saved to the database and loaded when the user returns to the dashboard. Users can clear their chat history.

**Independent Test**: Send messages, refresh the page, and verify previous messages are still visible.

### Implementation for User Story 4

- [x] T016 [US4] Add GET `/{user_id}/chat/history` endpoint in `backend/app/routes/chat.py` — returns last N messages (default 50, max 100) ordered by created_at, with JWT auth and owner validation
- [x] T017 [US4] Add DELETE `/{user_id}/chat/history` endpoint in `backend/app/routes/chat.py` — deletes all chat messages for the user, returns 204
- [x] T018 [P] [US4] Add `getChatHistory(userId, token, limit?)` and `clearChatHistory(userId, token)` methods to `frontend/src/lib/api.ts`
- [x] T019 [US4] Update `ChatPanel` in `frontend/src/components/ChatPanel.tsx` — load chat history on mount via `getChatHistory`, add "Clear chat" button that calls `clearChatHistory` and resets local state, show loaded history messages on initial render

**Checkpoint**: Chat history persists across page refreshes. Users can clear their history.

---

## Phase 7: User Story 5 — Multi-Provider AI Support (Priority: P3)

**Goal**: Support Groq as an alternative AI provider, switchable via environment variable, with automatic fallback.

**Independent Test**: Set `AI_PROVIDER=groq` in backend/.env, send a chat message, and verify a response is returned from Groq.

### Implementation for User Story 5

- [x] T020 [US5] Add `GroqProvider` class in `backend/app/ai_provider.py` — uses `groq` SDK with model `llama-3.3-70b-versatile`, same `chat(messages, tools)` interface as OpenAIProvider
- [x] T021 [US5] Add fallback logic in `backend/app/ai_provider.py` — if primary provider fails (API error, timeout), try the secondary provider; update `get_provider()` to accept fallback parameter

**Checkpoint**: System works with either OpenAI or Groq. Provider is configurable via environment variable with automatic fallback.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Validation, error handling improvements, and E2E verification

- [x] T022 Add message length validation in `backend/app/routes/chat.py` — reject messages >2000 characters with 422 error
- [x] T023 Add tool call safety limit in `backend/app/routes/chat.py` — max 5 tool calls per request, 30-second timeout on AI provider calls
- [x] T024 [P] Add welcome message logic in `backend/app/routes/chat.py` or `frontend/src/components/ChatPanel.tsx` — show initial greeting explaining what the chatbot can do when chat is empty
- [x] T025 [P] Update `specs/001-ai-chatbot/quickstart.md` with final setup instructions and verification steps
- [x] T026 E2E validation: test chat create, list, complete, delete, and update tasks via curl against running servers
- [x] T027 E2E validation: test chat history GET and DELETE endpoints via curl
- [x] T028 Manual validation: test conversational flow in browser (ambiguous messages, error scenarios, rapid messages)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (T004-T008) — core chat endpoint
- **US2 (Phase 4)**: Depends on US1 (T009-T011) — needs working chat endpoint for the UI
- **US3 (Phase 5)**: Depends on US1 (T009-T011) — enhances existing chat prompt
- **US4 (Phase 6)**: Depends on US2 (T012-T013) — needs ChatPanel for history UI
- **US5 (Phase 7)**: Depends on Foundational (T004) — extends ai_provider.py
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational only — the core MVP
- **US2 (P1)**: Depends on US1 — needs working backend to connect UI to
- **US3 (P2)**: Depends on US1 — enhances the system prompt
- **US4 (P3)**: Depends on US2 — needs ChatPanel to show history
- **US5 (P3)**: Independent of other stories — only extends ai_provider.py

### Parallel Opportunities

Within Foundational phase, T005-T008 can all run in parallel (different files):
- T005: chat_tools.py
- T006: models.py
- T007: schemas.py
- T008: chat.ts

US4 (T018) and US5 can run in parallel with each other after their respective dependencies are met.

---

## Parallel Example: Foundational Phase

```bash
# After T004 (ai_provider.py) is complete, launch in parallel:
Task: "T005 - Create tool definitions in backend/app/chat_tools.py"
Task: "T006 - Add ChatMessage model in backend/app/models.py"
Task: "T007 - Add ChatRequest/ChatResponse schemas in backend/app/schemas.py"
Task: "T008 - Create chat types in frontend/src/types/chat.ts"
```

## Parallel Example: US4 + US5

```bash
# After US2 is complete:
Task: "T016-T019 - US4: Chat history persistence"
Task: "T020-T021 - US5: Multi-provider support"
# These can run in parallel as they touch different files
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T008)
3. Complete Phase 3: US1 — Chat endpoint (T009-T011)
4. Complete Phase 4: US2 — Chat UI (T012-T013)
5. **STOP and VALIDATE**: Test chat create/list/complete/delete in browser
6. Deploy/demo — users can manage tasks via chat

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Backend chat works via curl (MVP backend)
3. Add US2 → Full chat UI on dashboard (MVP frontend)
4. Add US3 → Smart task queries
5. Add US4 → Chat history persistence
6. Add US5 → Groq provider support
7. Each story adds value without breaking previous stories

---

## Summary

| Phase | Tasks | Parallel |
|-------|-------|----------|
| Setup | 3 (T001-T003) | 0 |
| Foundational | 5 (T004-T008) | 4 |
| US1: NL Task CRUD | 3 (T009-T011) | 0 |
| US2: Chat UI | 2 (T012-T013) | 0 |
| US3: Smart Queries | 2 (T014-T015) | 0 |
| US4: Chat History | 4 (T016-T019) | 1 |
| US5: Multi-Provider | 2 (T020-T021) | 0 |
| Polish | 7 (T022-T028) | 2 |
| **Total** | **28** | **7** |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently testable after its checkpoint
- MVP scope: Phases 1-4 (13 tasks) delivering chat endpoint + chat UI
- Commit after each task or logical group
