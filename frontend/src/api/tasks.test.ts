import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "./client";
import { fetchTasks } from "./tasks";

function mockFetchOnce(status: number, body: unknown) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () => Promise.resolve(body),
    }),
  );
}

describe("fetchTasks", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("returns the parsed task list on success", async () => {
    const tasks = [{ id: "1", title: "A task", status: "pending" }];
    mockFetchOnce(200, tasks);

    const result = await fetchTasks("fake-token");

    expect(result).toEqual(tasks);
    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/tasks"),
      expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer fake-token" }) }),
    );
  });

  it("throws an ApiError with the server's error code and message on failure", async () => {
    mockFetchOnce(403, { error: "forbidden", message: "Only managers can create tasks" });

    await expect(fetchTasks("fake-token")).rejects.toMatchObject({
      status: 403,
      code: "forbidden",
      message: "Only managers can create tasks",
    });
  });

  it("throws a network ApiError when fetch itself fails", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));

    await expect(fetchTasks("fake-token")).rejects.toBeInstanceOf(ApiError);
  });
});
