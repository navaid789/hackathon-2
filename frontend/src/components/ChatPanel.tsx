"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { api } from "@/lib/api";
import type { ChatMessage, ChatSession } from "@/types/chat";
import TaskCard from "@/components/TaskCard";

interface ChatPanelProps {
  userId: string;
  getToken: () => Promise<string>;
  onTaskAction?: () => void;
}

function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function parseTaskData(raw?: string | null): Record<string, unknown> | null {
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export default function ChatPanel({ userId, getToken, onTaskAction }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<number | null>(null);
  const [showSessions, setShowSessions] = useState(false);
  const [sessionsLoaded, setSessionsLoaded] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Load sessions on mount
  const loadSessions = useCallback(async () => {
    try {
      const token = await getToken();
      const list = await api.listChatSessions(userId, token);
      setSessions(list);
      // Auto-select most recent session if none active
      if (list.length > 0 && activeSessionId === null) {
        setActiveSessionId(list[0].id);
      }
    } catch {
      // Silently fail
    } finally {
      setSessionsLoaded(true);
    }
  }, [userId, getToken, activeSessionId]);

  useEffect(() => {
    loadSessions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId]);

  // Load messages when active session changes
  useEffect(() => {
    if (!activeSessionId || !sessionsLoaded) {
      if (sessionsLoaded && !activeSessionId) {
        setMessages([]);
      }
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const token = await getToken();
        const msgs = await api.getSessionMessages(userId, token, activeSessionId);
        if (!cancelled) setMessages(msgs);
      } catch {
        if (!cancelled) setMessages([]);
      }
    })();
    return () => { cancelled = true; };
  }, [activeSessionId, sessionsLoaded, userId, getToken]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: ChatMessage = {
      id: Date.now(),
      user_id: userId,
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const token = await getToken();
      const response = await api.sendMessage(userId, token, text, activeSessionId);

      // If this was a new session, store the returned session_id
      if (!activeSessionId && response.session_id) {
        setActiveSessionId(response.session_id);
        // Refresh session list
        const list = await api.listChatSessions(userId, token);
        setSessions(list);
      }

      const assistantMsg: ChatMessage = {
        id: Date.now() + 1,
        user_id: userId,
        role: "assistant",
        content: response.reply,
        session_id: response.session_id,
        task_data: response.task_data ? JSON.stringify(response.task_data) : null,
        action_taken: response.action_taken ?? null,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMsg]);

      if (response.action_taken && onTaskAction) {
        onTaskAction();
      }
    } catch {
      const errorMsg: ChatMessage = {
        id: Date.now() + 1,
        user_id: userId,
        role: "assistant",
        content: "I'm having trouble connecting right now. Please try again in a moment.",
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setShowSessions(false);
  };

  const handleSelectSession = (sessionId: number) => {
    setActiveSessionId(sessionId);
    setShowSessions(false);
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation();
    try {
      const token = await getToken();
      await api.deleteChatSession(userId, token, sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        setActiveSessionId(null);
        setMessages([]);
      }
    } catch {
      // Silently fail
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 relative">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-200">
          TaskFlow AI
        </h2>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setShowSessions(!showSessions)}
            className={`text-xs px-2.5 py-1 rounded-md transition-colors ${
              showSessions
                ? "text-indigo-700 bg-indigo-100 dark:text-indigo-300 dark:bg-indigo-900/40 font-medium"
                : "text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800"
            }`}
          >
            Sessions
          </button>
          <button
            onClick={handleNewChat}
            className="text-xs px-2.5 py-1 rounded-md transition-colors text-indigo-600 bg-indigo-50 hover:bg-indigo-100 dark:text-indigo-400 dark:bg-indigo-900/30 dark:hover:bg-indigo-900/50 font-medium"
          >
            New Chat
          </button>
        </div>
      </div>

      {/* Session list overlay */}
      {showSessions && (
        <div className="absolute top-[49px] left-0 right-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 max-h-64 overflow-y-auto shadow-lg">
          {sessions.length === 0 ? (
            <div className="px-4 py-3 text-xs text-gray-400 text-center">No sessions yet</div>
          ) : (
            sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={`flex items-center justify-between px-4 py-2.5 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                  s.id === activeSessionId ? "bg-indigo-50 dark:bg-indigo-900/20" : ""
                }`}
              >
                <div className="flex-1 min-w-0 mr-2">
                  <div className="text-sm text-gray-800 dark:text-gray-200 truncate">
                    {s.title}
                  </div>
                  <div className="text-xs text-gray-400">{timeAgo(s.updated_at)}</div>
                </div>
                <button
                  onClick={(e) => handleDeleteSession(e, s.id)}
                  className="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 p-1"
                  title="Delete session"
                >
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {sessionsLoaded && messages.length === 0 && (
          <div className="text-center text-gray-400 dark:text-gray-500 text-sm mt-8">
            <p className="font-medium mb-2">Hi! I&apos;m TaskFlow AI</p>
            <p>I can help you manage your tasks. Try:</p>
            <ul className="mt-2 space-y-1 text-xs">
              <li>&quot;Add a task to buy groceries&quot;</li>
              <li>&quot;Show my tasks&quot;</li>
              <li>&quot;Mark buy groceries as done&quot;</li>
              <li>&quot;How many tasks do I have left?&quot;</li>
            </ul>
          </div>
        )}

        {messages.map((msg) => {
          const taskData = msg.role === "assistant" ? parseTaskData(msg.task_data) : null;
          return (
            <div
              key={msg.id}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-2 text-sm ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-br-md"
                    : "bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 rounded-bl-md"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>
                {taskData && (
                  <TaskCard
                    taskData={taskData as Record<string, unknown>}
                    actionTaken={msg.action_taken}
                  />
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl rounded-bl-md px-4 py-2 text-sm text-gray-400">
              <span className="inline-flex gap-1">
                <span className="animate-bounce" style={{ animationDelay: "0ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "150ms" }}>.</span>
                <span className="animate-bounce" style={{ animationDelay: "300ms" }}>.</span>
              </span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 dark:border-gray-700 p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message..."
            disabled={loading}
            className="flex-1 rounded-full border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-800 dark:text-gray-200 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="rounded-full bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
