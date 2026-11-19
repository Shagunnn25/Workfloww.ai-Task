import { describe, expect, it } from "vitest";
import type { Task } from "../types/task";
import { filterTasksByStatus } from "./taskFilters";

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

describe("filterTasksByStatus", () => {
  const tasks = [
    makeTask({ id: "1", status: "pending" }),
    makeTask({ id: "2", status: "in_progress" }),
    makeTask({ id: "3", status: "completed" }),
    makeTask({ id: "4", status: "completed" }),
  ];

  it("returns only tasks matching the given status", () => {
    expect(filterTasksByStatus(tasks, "completed").map((t) => t.id)).toEqual(["3", "4"]);
  });

  it("returns all tasks when status is 'all'", () => {
    expect(filterTasksByStatus(tasks, "all")).toHaveLength(4);
  });

  it("returns an empty array when nothing matches", () => {
    expect(filterTasksByStatus([], "pending")).toEqual([]);
  });
});
