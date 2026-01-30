import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, col

from app.db import get_session
from app.models import Task, ChatMessage
from app.schemas import ChatRequest, ChatResponse
from app.auth import verify_token, get_user_id
from app.ai_provider import get_provider
from app.chat_tools import TOOLS, execute_tool

router = APIRouter(prefix="/api")

MAX_TOOL_CALLS = 5
MAX_MESSAGE_LENGTH = 2000


def _require_owner(token_payload: dict, url_user_id: str) -> str:
    user_id = get_user_id(token_payload)
    if user_id != url_user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return user_id


def _build_system_prompt(tasks: list[Task]) -> str:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.completed)
    incomplete = total - completed

    today = datetime.now(timezone.utc).date()
    completed_today = [
        t for t in tasks
        if t.completed and t.updated_at and t.updated_at.date() == today
    ]

    task_summary = ""
    if tasks:
        task_lines = []
        for t in tasks:
            status = "done" if t.completed else "todo"
            task_lines.append(f"  - [id={t.id}] [{status}] {t.title}" + (f" — {t.description}" if t.description else ""))
        task_summary = "\n".join(task_lines)
    else:
        task_summary = "  (no tasks yet)"

    today_summary = ""
    if completed_today:
        today_lines = [f"  - {t.title}" for t in completed_today]
        today_summary = f"\n\nCompleted today:\n" + "\n".join(today_lines)

    return f"""You are TaskFlow AI, a helpful task management assistant. You help users manage their todo tasks through natural language.

You can:
- Create new tasks
- List all tasks
- Mark tasks as complete/incomplete
- Delete tasks
- Update task titles and descriptions
- Answer questions about the user's tasks

Current task summary: {total} total, {completed} completed, {incomplete} incomplete.

Current tasks:
{task_summary}{today_summary}

When the user asks to do something with a task, use the appropriate tool. When they ask a question about their tasks, answer based on the task list above. Always be friendly and concise.

Important: When creating a task, extract a clean title from the user's message. For example, "add a task to buy groceries" should create a task titled "Buy groceries", not "a task to buy groceries"."""


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

    # Fetch user's current tasks for context
    tasks = session.exec(select(Task).where(Task.user_id == user_id)).all()

    # Build conversation messages
    system_prompt = _build_system_prompt(list(tasks))

    # Load recent chat history for context
    recent_messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.user_id == user_id)
        .order_by(col(ChatMessage.created_at).desc())
        .limit(10)
    ).all()
    recent_messages = list(reversed(recent_messages))

    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    for msg in recent_messages:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": body.message})

    # Save user message
    user_msg = ChatMessage(user_id=user_id, role="user", content=body.message)
    session.add(user_msg)
    session.commit()

    # Call AI provider with tool loop
    provider = get_provider()
    action_taken = None
    task_data = None

    for _ in range(MAX_TOOL_CALLS):
        try:
            response = provider.chat(messages, TOOLS)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"AI provider call failed: {type(e).__name__}: {e}")
            # Try fallback provider
            try:
                provider = get_provider(fallback=True)
                response = provider.chat(messages, TOOLS)
            except Exception as e2:
                logging.getLogger(__name__).error(f"Fallback also failed: {type(e2).__name__}: {e2}")
                # Save error message
                error_reply = "I'm having trouble connecting right now. Please try again in a moment."
                assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=error_reply)
                session.add(assistant_msg)
                session.commit()
                return ChatResponse(reply=error_reply)

        choice = response.choices[0]

        if choice.finish_reason == "tool_calls" or (choice.message.tool_calls and len(choice.message.tool_calls) > 0):
            # Process tool calls - only include fields supported by all providers
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
            reply = choice.message.content or "I'm not sure how to help with that. Try asking me to create, list, complete, delete, or update a task."

            # Save assistant message
            assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=reply)
            session.add(assistant_msg)
            session.commit()

            return ChatResponse(reply=reply, action_taken=action_taken, task_data=task_data)

    # If we exhausted tool calls, get a final response without tools
    response = provider.chat(messages, [])
    reply = response.choices[0].message.content or "I completed the actions you requested."

    assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=reply)
    session.add(assistant_msg)
    session.commit()

    return ChatResponse(reply=reply, action_taken=action_taken, task_data=task_data)


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
