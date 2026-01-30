"use client";

import { useEffect, useState, useCallback } from "react";
import { useSession, signOut, authClient } from "@/lib/auth-client";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Task } from "@/types/task";
import Link from "next/link";
import ChatPanel from "@/components/ChatPanel";

export default function Dashboard() {
  const { data: session, isPending } = useSession();
  const router = useRouter();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [chatOpen, setChatOpen] = useState(true);

  const loadTasks = useCallback(async () => {
    if (!session?.user) return;
    try {
      const res = await authClient.token();
      const jwt = (res as { data?: { token?: string } })?.data?.token;
      if (!jwt) return;
      const data = await api.listTasks(session.user.id, jwt);
      setTasks(data);
    } catch (err) {
      console.error("Failed to load tasks", err);
    }
  }, [session?.user]);

  useEffect(() => {
    if (!isPending && !session) {
      router.push("/sign-in");
    }
  }, [session, isPending, router]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  if (isPending) {
    return <div className="min-h-screen flex items-center justify-center text-gray-500">Loading...</div>;
  }

  if (!session) return null;

  async function getToken(): Promise<string> {
    const res = await authClient.token();
    const jwt = (res as { data?: { token?: string } })?.data?.token;
    if (!jwt) throw new Error("No token");
    return jwt;
  }

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    const token = await getToken();
    await api.createTask(session!.user.id, token, { title, description });
    setTitle("");
    setDescription("");
    loadTasks();
  }

  async function handleToggle(taskId: number) {
    const token = await getToken();
    await api.toggleComplete(session!.user.id, token, taskId);
    loadTasks();
  }

  async function handleDelete(taskId: number) {
    const token = await getToken();
    await api.deleteTask(session!.user.id, token, taskId);
    loadTasks();
  }

  function startEdit(task: Task) {
    setEditingId(task.id);
    setEditTitle(task.title);
    setEditDescription(task.description);
  }

  async function handleEdit(e: React.FormEvent) {
    e.preventDefault();
    if (editingId === null) return;
    const token = await getToken();
    await api.updateTask(session!.user.id, token, editingId, {
      title: editTitle,
      description: editDescription,
    });
    setEditingId(null);
    loadTasks();
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top nav */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
            TaskFlow
          </Link>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className="px-3 py-1.5 text-sm font-medium text-indigo-700 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
            >
              {chatOpen ? "Hide Chat" : "Show Chat"}
            </button>
            <span className="text-sm text-gray-500 hidden sm:inline">{session.user.email}</span>
            <button
              onClick={() => signOut().then(() => router.push("/"))}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Task list */}
        <main className={`flex-1 overflow-y-auto px-4 py-10 ${chatOpen ? "max-w-2xl" : "max-w-3xl mx-auto"}`}>
          <h1 className="text-2xl font-bold text-gray-900 mb-8">My Tasks</h1>

          {/* Add task form */}
          <form onSubmit={handleAdd} className="mb-8 p-5 bg-white rounded-xl shadow-sm border border-gray-100">
            <input
              type="text"
              placeholder="What needs to be done?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
            <input
              type="text"
              placeholder="Add a description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg mb-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
            <button
              type="submit"
              className="px-5 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Add Task
            </button>
          </form>

          {/* Task list */}
          <div className="space-y-3">
            {tasks.length === 0 && (
              <div className="text-center py-12">
                <div className="text-4xl mb-3">&#9745;</div>
                <p className="text-gray-400 text-sm">No tasks yet. Add one above or ask the AI chat to create one.</p>
              </div>
            )}
            {tasks.map((task) => (
              <div
                key={task.id}
                className="p-4 bg-white rounded-xl shadow-sm border border-gray-100 flex items-center gap-4 hover:shadow-md transition-shadow"
              >
                {editingId === task.id ? (
                  <form onSubmit={handleEdit} className="flex-1 space-y-2">
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <input
                      type="text"
                      value={editDescription}
                      onChange={(e) => setEditDescription(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <div className="flex gap-2">
                      <button type="submit" className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
                        Save
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingId(null)}
                        className="px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-200 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                ) : (
                  <>
                    <input
                      type="checkbox"
                      checked={task.completed}
                      onChange={() => handleToggle(task.id)}
                      className="w-5 h-5 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500 cursor-pointer"
                    />
                    <div className="flex-1 min-w-0">
                      <p className={`font-medium text-sm ${task.completed ? "line-through text-gray-400" : "text-gray-900"}`}>
                        {task.title}
                      </p>
                      {task.description && (
                        <p className="text-xs text-gray-400 mt-0.5 truncate">{task.description}</p>
                      )}
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <button
                        onClick={() => startEdit(task)}
                        className="px-3 py-1.5 text-xs font-medium text-indigo-700 bg-indigo-50 rounded-lg hover:bg-indigo-100 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDelete(task.id)}
                        className="px-3 py-1.5 text-xs font-medium text-red-700 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </main>

        {/* Chat panel */}
        {chatOpen && (
          <aside className="w-96 hidden md:flex flex-col border-l border-gray-200 bg-white">
            <ChatPanel
              userId={session.user.id}
              getToken={getToken}
              onTaskAction={loadTasks}
            />
          </aside>
        )}
      </div>

      {/* Mobile chat overlay */}
      {chatOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex flex-col bg-white">
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
            <span className="text-sm font-semibold text-gray-700">TaskFlow AI</span>
            <button
              onClick={() => setChatOpen(false)}
              className="text-sm text-gray-500 hover:text-gray-700"
            >
              Close
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatPanel
              userId={session.user.id}
              getToken={getToken}
              onTaskAction={loadTasks}
            />
          </div>
        </div>
      )}
    </div>
  );
}
