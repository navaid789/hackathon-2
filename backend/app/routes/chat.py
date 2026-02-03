import json
import re
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col

from app.db import get_session
from app.models import Task, ChatMessage, ChatSession
from app.schemas import ChatRequest, ChatResponse, ChatSessionResponse, ChatMessageResponse
from app.auth import verify_token, get_user_id
from app.ai_provider import get_provider
from app.chat_tools import TOOLS, execute_tool

router = APIRouter(prefix="/api")

MAX_TOOL_CALLS = 5
MAX_MESSAGE_LENGTH = 2000


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks from model output (Qwen3)."""
    if "<think>" in text:
        text = re.sub(r"<think>.*?</think>\s*", "", text, flags=re.DOTALL).strip()
    return text or "Done!"


def _require_owner(token_payload: dict, url_user_id: str) -> str:
    user_id = get_user_id(token_payload)
    if user_id != url_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id


def _build_system_prompt(tasks: list[Task]) -> str:
    now = datetime.now(timezone.utc)
    today = now.date()
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    incomplete = total - completed
    overdue = sum(1 for t in tasks if t.due_date and t.due_date.date() < today and not t.completed)
    due_today = sum(1 for t in tasks if t.due_date and t.due_date.date() == today and not t.completed)

    completed_today = [
        t for t in tasks
        if t.completed and t.updated_at and t.updated_at.date() == today
    ]

    task_summary = ""
    if tasks:
        task_lines = []
        for t in tasks:
            status = "done" if t.completed else "todo"
            parts = [f"[id={t.id}]", f"[{status}]", f"[{t.priority}]", t.title]
            if t.due_date:
                parts.append(f"(due: {t.due_date.strftime('%Y-%m-%d')})")
            if t.description:
                parts.append(f"— {t.description}")
            task_lines.append("  - " + " ".join(parts))
        task_summary = "\n".join(task_lines)
    else:
        task_summary = "  (no tasks yet)"

    today_summary = ""
    if completed_today:
        today_lines = [f"  - {t.title}" for t in completed_today]
        today_summary = f"\n\nCompleted today:\n" + "\n".join(today_lines)

    urgency = ""
    if overdue > 0 or due_today > 0:
        parts = []
        if overdue > 0:
            parts.append(f"{overdue} overdue")
        if due_today > 0:
            parts.append(f"{due_today} due today")
        urgency = f"\nUrgent: {', '.join(parts)}."

    return f"""You are TaskFlow AI, a helpful task management assistant. You help users manage their todo tasks through natural language.

You can:
- Create new tasks (with optional priority and due date)
- List all tasks
- Mark tasks as complete/incomplete
- Delete tasks
- Update task titles, descriptions, priority, and due dates
- Search tasks by keyword
- Filter tasks by status, priority, or due date (overdue/today/this_week)
- Mark all tasks as complete at once
- Delete all completed tasks at once
- Answer questions about the user's tasks

Current task summary: {total} total, {completed} completed, {incomplete} incomplete.{urgency}

Current tasks:
{task_summary}{today_summary}

When the user asks to do something with a task, use the appropriate tool. When they ask a question about their tasks, answer based on the task list above. Always be friendly and concise.

Priority levels: low, medium, high, urgent. Default is medium.

Important: When creating a task, extract a clean title from the user's message. For example, "add a task to buy groceries" should create a task titled "Buy groceries", not "a task to buy groceries". When the user specifies a priority or due date, pass those to the tool."""


@router.get("/{user_id}/chat/sessions", response_model=list[ChatSessionResponse])
def list_chat_sessions(
    user_id: str,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    sessions = session.exec(
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(col(ChatSession.updated_at).desc())
    ).all()
    return list(sessions)


@router.delete("/{user_id}/chat/sessions/{session_id}", status_code=204)
def delete_chat_session(
    user_id: str,
    session_id: int,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    chat_session = session.get(ChatSession, session_id)
    if not chat_session or chat_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete all messages in this session
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    for msg in messages:
        session.delete(msg)
    session.delete(chat_session)
    session.commit()


@router.get("/{user_id}/chat/sessions/{session_id}/messages", response_model=list[ChatMessageResponse])
def get_session_messages(
    user_id: str,
    session_id: int,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    chat_session = session.get(ChatSession, session_id)
    if not chat_session or chat_session.user_id != user_id:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(col(ChatMessage.created_at).asc())
    ).all()
    return list(messages)


@router.post("/{user_id}/chat")
def send_chat_message(
    user_id: str,
    body: ChatRequest,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)

    if len(body.message) > MAX_MESSAGE_LENGTH:
        raise HTTPException(status_code=422, detail=f"Message exceeds {MAX_MESSAGE_LENGTH} character limit")

    # Resolve or create session
    chat_session: ChatSession
    if body.session_id:
        found = session.get(ChatSession, body.session_id)
        if not found or found.user_id != user_id:
            raise HTTPException(status_code=404, detail="Session not found")
        chat_session = found
    else:
        title = body.message[:50].strip()
        if len(body.message) > 50:
            title += "..."
        chat_session = ChatSession(user_id=user_id, title=title)
        session.add(chat_session)
        session.commit()
        session.refresh(chat_session)

    # Fetch user's current tasks for context
    tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()

    # Build conversation messages
    system_prompt = _build_system_prompt(list(tasks))

    # Load recent chat history scoped to session
    recent_messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == chat_session.id)
        .order_by(col(ChatMessage.created_at).desc())
        .limit(10)
    ).all()
    recent_messages = list(reversed(recent_messages))

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in recent_messages:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    # Save user message
    user_msg = ChatMessage(user_id=user_id, role="user", content=body.message, session_id=chat_session.id)
    session.add(user_msg)
    session.commit()

    # Call AI provider with tool loop
    provider = get_provider()
    action_taken = None
    task_data = None

    import logging
    logger = logging.getLogger(__name__)

    # Keep a clean copy of the initial messages for fallback
    initial_messages = [m.copy() for m in messages]

    for _ in range(MAX_TOOL_CALLS):
        try:
            response = provider.chat(messages, TOOLS)
        except Exception as e:
            logger.error(f"AI provider call failed: {type(e).__name__}: {e}")
            # Try fallback provider with clean messages (not corrupted by failed tool calls)
            try:
                from app.ai_provider import OpenAIProvider, GroqProvider
                if isinstance(provider, GroqProvider):
                    provider = OpenAIProvider()
                else:
                    provider = GroqProvider()
                messages = [m.copy() for m in initial_messages]
                response = provider.chat(messages, TOOLS)
            except Exception as e2:
                logger.error(f"Fallback also failed: {type(e2).__name__}: {e2}")
                error_reply = "I'm having trouble connecting right now. Please try again in a moment."
                assistant_msg = ChatMessage(
                    user_id=user_id, role="assistant", content=error_reply,
                    session_id=chat_session.id,
                )
                session.add(assistant_msg)
                session.commit()
                return ChatResponse(reply=error_reply, session_id=chat_session.id)

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or (choice.message.tool_calls and len(choice.message.tool_calls) > 0):
            msg_dict = {"role": "assistant", "content": choice.message.content or ""}
            if choice.message.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in choice.message.tool_calls
                ]
            messages.append(msg_dict)

            for tool_call in choice.message.tool_calls:
                fn_name = tool_call.function.name
                fn_args = json.loads(tool_call.function.arguments)

                result_text, act, tdata = execute_tool(fn_name, fn_args, user_id, session)

                if act:
                    action_taken = act
                if tdata:
                    task_data = tdata

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_text,
                })
        else:
            # Final text response
            reply = _strip_thinking(choice.message.content or "I'm not sure how to help with that. Try asking me to create, list, complete, delete, or update a task.")

            # Save assistant message with task_data and action_taken
            assistant_msg = ChatMessage(
                user_id=user_id, role="assistant", content=reply,
                session_id=chat_session.id,
                task_data=json.dumps(task_data) if task_data else None,
                action_taken=action_taken,
            )
            session.add(assistant_msg)

            # Update session timestamp
            chat_session.updated_at = datetime.now(timezone.utc)
            session.add(chat_session)
            session.commit()

            return ChatResponse(reply=reply, session_id=chat_session.id, action_taken=action_taken, task_data=task_data)

    # If we exhausted tool calls, get a final response without tools
    response = provider.chat(messages, [])
    reply = _strip_thinking(response.choices[0].message.content or "I completed the actions you requested.")

    assistant_msg = ChatMessage(
        user_id=user_id, role="assistant", content=reply,
        session_id=chat_session.id,
        task_data=json.dumps(task_data) if task_data else None,
        action_taken=action_taken,
    )
    session.add(assistant_msg)

    chat_session.updated_at = datetime.now(timezone.utc)
    session.add(chat_session)
    session.commit()

    return ChatResponse(reply=reply, session_id=chat_session.id, action_taken=action_taken, task_data=task_data)


@router.get("/{user_id}/chat/history")
def get_chat_history(
    user_id: str,
    limit: int = 50,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    if limit > 100:
        limit = 100

    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(col(ChatMessage.created_at).desc())
        .limit(limit)
    ).all()

    return list(reversed(messages))


@router.delete("/{user_id}/chat/history", status_code=204)
def clear_chat_history(
    user_id: str,
    session: Session = Depends(get_session),
    token: dict = Depends(verify_token),
):
    _require_owner(token, user_id)
    messages = session.exec(
        select(ChatMessage).where(ChatMessage.user_id == user_id)
    ).all()
    for msg in messages:
        session.delete(msg)
    session.commit()
