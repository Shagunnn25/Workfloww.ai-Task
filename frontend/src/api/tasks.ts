import type { Task, TaskCreateInput, TaskStatus } from "../types/task";
import { apiRequest } from "./client";

export async function fetchTasks(token: string): Promise<Task[]> {
  return apiRequest<Task[]>("/tasks", { token });
}

export async function createTask(token: string, input: TaskCreateInput): Promise<Task> {
  return apiRequest<Task>("/tasks", { method: "POST", body: input, token });
}

export async function updateTaskStatus(token: string, taskId: string, status: TaskStatus): Promise<Task> {
  return apiRequest<Task>(`/tasks/${taskId}`, { method: "PATCH", body: { status }, token });
}
