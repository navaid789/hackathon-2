export interface Task {
  id: number;
  user_id: string;
  title: string;
  description: string;
  completed: boolean;
  priority: "low" | "medium" | "high" | "urgent";
  due_date: string | null;
  created_at: string;
  updated_at: string;
}
