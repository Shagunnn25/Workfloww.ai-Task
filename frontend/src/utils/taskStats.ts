import type { Task } from "../types/task";

export function calculateCompletionPercentage(tasks: Task[]): number {
  if (tasks.length === 0) {
    return 0;
  }
  const completed = tasks.filter((task) => task.status === "completed").length;
  return Math.round((completed / tasks.length) * 100);
}
