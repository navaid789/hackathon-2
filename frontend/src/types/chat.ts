export interface ChatMessage {
  id: number;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  session_id?: number | null;
  task_data?: string | null;
  action_taken?: string | null;
  created_at: string;
}

export interface ChatResponse {
  reply: string;
  session_id: number;
  action_taken?: string | null;
  task_data?: Record<string, unknown> | null;
}

export interface ChatSession {
  id: number;
  user_id: string;
  title: string;
  created_at: string;
  updated_at: string;
}
