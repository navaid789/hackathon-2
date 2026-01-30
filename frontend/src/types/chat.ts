export interface ChatMessage {
  id: number;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface ChatResponse {
  reply: string;
  action_taken?: string | null;
  task_data?: Record<string, unknown> | null;
}
