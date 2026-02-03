"use client";

interface TaskCardData {
  id?: number;
  title?: string;
  description?: string;
  priority?: string;
  completed?: boolean;
  due_date?: string | null;
}

interface TaskCardProps {
  taskData: TaskCardData;
  actionTaken?: string | null;
}

const priorityColors: Record<string, { bg: string; text: string }> = {
  urgent: { bg: "bg-red-100 dark:bg-red-900/30", text: "text-red-700 dark:text-red-400" },
  high: { bg: "bg-orange-100 dark:bg-orange-900/30", text: "text-orange-700 dark:text-orange-400" },
  medium: { bg: "bg-blue-100 dark:bg-blue-900/30", text: "text-blue-700 dark:text-blue-400" },
  low: { bg: "bg-gray-100 dark:bg-gray-700", text: "text-gray-600 dark:text-gray-400" },
};

function actionLabel(action?: string | null): string {
  if (!action) return "Task";
  if (action.includes("created")) return "Task Created";
  if (action.includes("completed") || action.includes("complete")) return "Task Completed";
  if (action.includes("deleted") || action.includes("delete")) return "Task Deleted";
  if (action.includes("updated") || action.includes("update")) return "Task Updated";
  return "Task";
}

function isOverdue(dueDate?: string | null): boolean {
  if (!dueDate) return false;
  return new Date(dueDate) < new Date();
}

function formatDate(dueDate: string): string {
  return new Date(dueDate).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export default function TaskCard({ taskData, actionTaken }: TaskCardProps) {
  const priority = taskData.priority || "medium";
  const colors = priorityColors[priority] || priorityColors.medium;
  const overdue = !taskData.completed && isOverdue(taskData.due_date);
  const label = actionLabel(actionTaken);

  return (
    <div className="mt-2 border border-gray-200 dark:border-gray-600 rounded-lg p-3 bg-white dark:bg-gray-850">
      {/* Action label */}
      <div className="text-xs font-medium text-indigo-600 dark:text-indigo-400 mb-1.5">
        {label}
      </div>

      {/* Title */}
      {taskData.title && (
        <div className="font-semibold text-sm text-gray-900 dark:text-gray-100">
          {taskData.title}
        </div>
      )}

      {/* Meta row */}
      <div className="flex items-center gap-2 mt-1.5 flex-wrap">
        {/* Priority badge */}
        <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${colors.bg} ${colors.text}`}>
          {priority}
        </span>

        {/* Status */}
        <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
          {taskData.completed ? (
            <>
              <svg className="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Done
            </>
          ) : (
            <>
              <svg className="w-3.5 h-3.5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" strokeWidth={2} />
              </svg>
              To Do
            </>
          )}
        </span>

        {/* Due date */}
        {taskData.due_date && (
          <span className={`text-xs ${overdue ? "text-red-500 font-medium" : "text-gray-500 dark:text-gray-400"}`}>
            Due {formatDate(taskData.due_date)}
          </span>
        )}
      </div>
    </div>
  );
}
