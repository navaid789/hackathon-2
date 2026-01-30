# Research Notes: AI Chatbot

**Feature**: `001-ai-chatbot` | **Date**: 2026-01-30

## R-001: OpenAI Function Calling API (2025-2026)

**Decision**: Use OpenAI `tools` parameter with strict mode for function calling.

**Rationale**: The `functions` parameter is deprecated. The `tools` parameter with `strict: true` ensures reliable schema adherence. The `pydantic_function_tool()` utility can auto-generate JSON schemas from Pydantic models.

**Alternatives considered**:
- Free-text parsing of AI responses → fragile, error-prone
- OpenAI Assistants API → too heavyweight for this use case, adds complexity
- Custom prompt engineering without function calling → unreliable action detection

**Source**: [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)

## R-002: Groq API OpenAI Compatibility

**Decision**: Use Groq Python SDK which is OpenAI-compatible for tool calling.

**Rationale**: Groq's API follows the same tool-calling structure as OpenAI. The `groq` Python SDK mirrors the `openai` SDK interface. Switching providers requires only changing the client initialization and model name. Model: `llama-3.3-70b-versatile` supports tool use.

**Alternatives considered**:
- Direct HTTP calls to Groq API → unnecessary when SDK exists
- Using OpenAI SDK with Groq base_url → works but loses Groq-specific features

**Source**: [Groq Tool Use Docs](https://console.groq.com/docs/tool-use), [Groq Python SDK](https://github.com/groq/groq-python)

## R-003: AI Provider Abstraction Pattern

**Decision**: Create a simple Protocol-based abstraction with `chat(messages, tools)` method.

**Rationale**: Both OpenAI and Groq SDKs use nearly identical interfaces for chat completions with tools. A thin abstraction (Protocol class) allows swapping providers via environment variable without changing business logic. No need for a heavy adapter pattern.

**Alternatives considered**:
- LangChain/LlamaIndex → too heavy for simple tool calling; adds large dependency tree
- No abstraction (hardcode OpenAI) → blocks Groq support without refactoring
- LiteLLM → good option but adds another dependency; direct SDK is simpler for 2 providers

## R-004: Chat Context Strategy

**Decision**: Include user's current task list + last 10 messages in each AI call.

**Rationale**: The AI needs task context to answer queries ("How many tasks left?") and to resolve references ("delete the groceries task"). Fresh task fetch per request ensures accuracy. Last 10 messages provide conversational continuity without excessive token usage (~2000 tokens per request).

**Alternatives considered**:
- Full conversation history → token limit issues, higher cost
- No task context → AI can't answer task queries or resolve references
- Embeddings/RAG for task search → overkill for <100 tasks per user

## R-005: Chat Message Persistence

**Decision**: Store chat messages in a `chat_messages` PostgreSQL table via SQLModel.

**Rationale**: Follows the existing pattern (Task model in SQLModel + Neon PostgreSQL). Enables history persistence across page refreshes. Simple schema: id, user_id, role, content, created_at. Auto-created on startup like the tasks table.

**Alternatives considered**:
- LocalStorage only → lost on device switch, no server backup
- Redis → adds infrastructure; PostgreSQL already available
- No persistence (session only) → works for MVP but poor UX on refresh

## R-006: Frontend Chat UI Pattern

**Decision**: Side panel on the dashboard page, collapsible on mobile.

**Rationale**: Keeps tasks and chat visible simultaneously. Users can see task list update in real-time when chat creates/completes tasks. Side panel is a common pattern in productivity apps (Slack, Notion). On mobile, the panel slides over the task list.

**Alternatives considered**:
- Separate /chat page → loses task list context; poor UX
- Floating bubble widget → feels disconnected from task management
- Bottom drawer → limited vertical space for message history

## R-007: Tool Call Safety Limits

**Decision**: Max 5 tool calls per request, 30-second timeout.

**Rationale**: Prevents infinite loops where the AI keeps calling tools. In practice, a single user message should trigger 0-2 tool calls. The 5-call limit is generous but safe. The 30-second timeout covers AI latency + tool execution.

**Alternatives considered**:
- No limits → risk of runaway costs and infinite loops
- Stricter limits (1-2 calls) → blocks legitimate multi-step requests ("create 3 tasks")
