import type { Task } from "@/types/task";
import type { ChatMessage, ChatResponse, ChatSession } from "@/types/chat";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchWithAuth(url: string, token: string, options: RequestInit = {}) {
  const res = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (res.status === 204) return null;
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  return res.json();
}

export const api = {
  listTasks: (userId: string, token: string): Promise<Task[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks`, token),

  createTask: (userId: string, token: string, data: { title: string; description?: string; priority?: string; due_date?: string | null }): Promise<Task> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks`, token, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateTask: (userId: string, token: string, taskId: number, data: { title?: string; description?: string; priority?: string; due_date?: string | null }): Promise<Task> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks/${taskId}`, token, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteTask: (userId: string, token: string, taskId: number): Promise<null> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks/${taskId}`, token, {
      method: "DELETE",
    }),

  toggleComplete: (userId: string, token: string, taskId: number): Promise<Task> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks/${taskId}/complete`, token, {
      method: "PATCH",
    }),

  // Chat sessions
  listChatSessions: (userId: string, token: string): Promise<ChatSession[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/sessions`, token),

  deleteChatSession: (userId: string, token: string, sessionId: number): Promise<null> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/sessions/${sessionId}`, token, {
      method: "DELETE",
    }),

  getSessionMessages: (userId: string, token: string, sessionId: number): Promise<ChatMessage[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/sessions/${sessionId}/messages`, token),

  // Chat messaging
  sendMessage: (userId: string, token: string, message: string, sessionId?: number | null): Promise<ChatResponse> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat`, token, {
      method: "POST",
      body: JSON.stringify({ message, session_id: sessionId ?? null }),
    }),

  getChatHistory: (userId: string, token: string, limit: number = 50): Promise<ChatMessage[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/history?limit=${limit}`, token),

  clearChatHistory: (userId: string, token: string): Promise<null> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/history`, token, {
      method: "DELETE",
    }),
};
