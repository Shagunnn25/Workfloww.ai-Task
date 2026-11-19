import type { Task, TaskStatus } from "../types/task";

export function filterTasksByStatus(tasks: Task[], status: TaskStatus | "all"): Task[] {
  if (status === "all") {
    return tasks;
  }
  return tasks.filter((task) => task.status === status);
}
