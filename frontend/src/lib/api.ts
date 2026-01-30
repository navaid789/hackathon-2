import type { Task } from "@/types/task";
import type { ChatMessage, ChatResponse } from "@/types/chat";

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
  if (!res.ok) {
    throw new Error(`API error: ${res.status}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  listTasks: (userId: string, token: string): Promise<Task[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks`, token),

  createTask: (userId: string, token: string, data: { title: string; description?: string }): Promise<Task> =>
    fetchWithAuth(`${API_URL}/api/${userId}/tasks`, token, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  updateTask: (userId: string, token: string, taskId: number, data: { title?: string; description?: string }): Promise<Task> =>
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

  sendMessage: (userId: string, token: string, message: string): Promise<ChatResponse> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat`, token, {
      method: "POST",
      body: JSON.stringify({ message }),
    }),

  getChatHistory: (userId: string, token: string, limit: number = 50): Promise<ChatMessage[]> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/history?limit=${limit}`, token),

  clearChatHistory: (userId: string, token: string): Promise<null> =>
    fetchWithAuth(`${API_URL}/api/${userId}/chat/history`, token, {
      method: "DELETE",
    }),
};
