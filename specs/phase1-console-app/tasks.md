# Tasks: Phase I - Todo Console Application

**Input**: Design documents from `/specs/phase1-console-app/`
**Prerequisites**: plan.md (required), spec.md (required)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Initialize UV project with pyproject.toml
- [ ] T002 [P] Create project directory structure (src/todo/, main.py)
- [ ] T003 [P] Create README.md with setup and usage instructions

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core models and storage that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [ ] T004 Create Task dataclass model in src/todo/models.py
- [ ] T005 Create TaskNotFoundError and ValidationError exceptions in src/todo/exceptions.py
- [ ] T006 Create TaskStore class in src/todo/store.py (in-memory storage with CRUD)
- [ ] T007 Create TaskService class skeleton in src/todo/services.py

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - Add a New Task (Priority: P1)

**Goal**: Users can add tasks with title and optional description

**Independent Test**: Run app, use `add "Task title"` command, verify task created

### Implementation for User Story 1

- [ ] T008 [US1] Implement TaskService.create_task() method in src/todo/services.py
- [ ] T009 [US1] Implement CLI command handler cmd_add() in src/todo/cli.py
- [ ] T010 [US1] Add input validation (empty title check) in services.py

**Checkpoint**: User Story 1 complete - can add tasks via CLI

---

## Phase 4: User Story 2 - View All Tasks (Priority: P1)

**Goal**: Users can see all their tasks in a formatted list

**Independent Test**: Add tasks, run `list` command, verify all tasks displayed

### Implementation for User Story 2

- [ ] T011 [US2] Implement TaskService.list_tasks() method in src/todo/services.py
- [ ] T012 [US2] Implement CLI command handler cmd_list() in src/todo/cli.py
- [ ] T013 [US2] Format task output with status indicators ([x] / [ ])

**Checkpoint**: User Stories 1 & 2 complete - can add and list tasks

---

## Phase 5: User Story 3 - Mark Task as Complete (Priority: P2)

**Goal**: Users can mark tasks as complete or incomplete

**Independent Test**: Add task, run `complete 1`, verify status changes in list

### Implementation for User Story 3

- [ ] T014 [US3] Implement TaskService.complete_task() method in src/todo/services.py
- [ ] T015 [US3] Implement TaskService.uncomplete_task() method in src/todo/services.py
- [ ] T016 [US3] Implement CLI command handlers cmd_complete() and cmd_uncomplete() in src/todo/cli.py

**Checkpoint**: User Story 3 complete - can mark tasks complete/incomplete

---

## Phase 6: User Story 4 - Delete Task (Priority: P2)

**Goal**: Users can delete tasks from their list

**Independent Test**: Add task, run `delete 1`, verify task removed from list

### Implementation for User Story 4

- [ ] T017 [US4] Implement TaskService.delete_task() method in src/todo/services.py
- [ ] T018 [US4] Implement CLI command handler cmd_delete() in src/todo/cli.py

**Checkpoint**: User Story 4 complete - can delete tasks

---

## Phase 7: User Story 5 - Update Task (Priority: P3)

**Goal**: Users can update task title and description

**Independent Test**: Add task, run `update 1 title "New title"`, verify change

### Implementation for User Story 5

- [ ] T019 [US5] Implement TaskService.update_task() method in src/todo/services.py
- [ ] T020 [US5] Implement CLI command handler cmd_update() in src/todo/cli.py

**Checkpoint**: User Story 5 complete - can update tasks

---

## Phase 8: User Story 6 - View Single Task Details (Priority: P3)

**Goal**: Users can view full details of a specific task

**Independent Test**: Add task with description, run `view 1`, verify all fields shown

### Implementation for User Story 6

- [ ] T021 [US6] Implement TaskService.get_task() method in src/todo/services.py
- [ ] T022 [US6] Implement CLI command handler cmd_view() in src/todo/cli.py
- [ ] T023 [US6] Format detailed task output with all fields and timestamps

**Checkpoint**: User Story 6 complete - can view task details

---

## Phase 9: CLI Polish

**Purpose**: Help, exit, error handling, and overall polish

- [ ] T024 Implement cmd_help() with all command documentation in src/todo/cli.py
- [ ] T025 Implement exit/quit handling in CLI main loop
- [ ] T026 Add graceful Ctrl+C (KeyboardInterrupt) handling
- [ ] T027 Implement unknown command handling with help suggestion
- [ ] T028 Create main.py entry point to launch CLI
- [ ] T029 Add package __init__.py files

**Checkpoint**: All features complete and polished

---

## Phase 10: Final Polish

**Purpose**: Documentation and testing

- [ ] T030 Update README.md with complete usage examples
- [ ] T031 Manual testing of all acceptance scenarios from spec.md
- [ ] T032 Code cleanup - ensure PEP 8 compliance

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - start immediately
- **Phase 2 (Foundation)**: Depends on Phase 1 - BLOCKS all user stories
- **Phases 3-8 (User Stories)**: All depend on Phase 2 completion
- **Phase 9 (CLI Polish)**: Depends on core user stories (3-6)
- **Phase 10 (Final)**: Depends on all previous phases

### Execution Order (Sequential Implementation)

```
T001 → T002, T003 (parallel)
    ↓
T004 → T005 → T006 → T007
    ↓
T008 → T009 → T010 (US1: Add)
    ↓
T011 → T012 → T013 (US2: List)
    ↓
T014 → T015 → T016 (US3: Complete)
    ↓
T017 → T018 (US4: Delete)
    ↓
T019 → T020 (US5: Update)
    ↓
T021 → T022 → T023 (US6: View)
    ↓
T024 → T025 → T026 → T027 → T028 → T029 (Polish)
    ↓
T030 → T031 → T032 (Final)
```

---

## Notes

- Each user story can be tested independently after its phase completes
- Commit after completing each phase
- Run manual tests against spec.md acceptance scenarios
- Focus on clean, readable output for all commands
