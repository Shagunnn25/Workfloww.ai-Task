import { describe, expect, it } from "vitest";
import type { Task } from "../types/task";
import { calculateCompletionPercentage } from "./taskStats";

function makeTask(overrides: Partial<Task>): Task {
  return {
    id: "1",
    company_id: "c1",
    title: "Task",
    description: null,
    status: "pending",
    assigned_to: "u1",
    assignee_name: "User One",
    created_by: "m1",
    due_date: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

describe("calculateCompletionPercentage", () => {
  it("returns 0 for an empty list", () => {
    expect(calculateCompletionPercentage([])).toBe(0);
  });

  it("returns 0 when no tasks are completed", () => {
    const tasks = [makeTask({ status: "pending" }), makeTask({ status: "in_progress" })];
    expect(calculateCompletionPercentage(tasks)).toBe(0);
  });

  it("returns 100 when all tasks are completed", () => {
    const tasks = [makeTask({ status: "completed" }), makeTask({ status: "completed" })];
    expect(calculateCompletionPercentage(tasks)).toBe(100);
  });

  it("rounds to the nearest whole percent", () => {
    const tasks = [
      makeTask({ status: "completed" }),
      makeTask({ status: "pending" }),
      makeTask({ status: "pending" }),
    ];
    expect(calculateCompletionPercentage(tasks)).toBe(33);
  });
});
