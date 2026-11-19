import { useEffect, useState } from "react";
import { ApiError } from "../api/client";
import { fetchTasks, updateTaskStatus } from "../api/tasks";
import { useAuth } from "../context/AuthContext";
import type { Task, TaskStatus } from "../types/task";
import { filterTasksByStatus } from "../utils/taskFilters";
import { calculateCompletionPercentage } from "../utils/taskStats";
import { StatusFilter } from "./StatusFilter";

type LoadState = "loading" | "success" | "error";

const STATUS_OPTIONS: TaskStatus[] = ["pending", "in_progress", "completed"];

export function EmployeeView() {
  const { session } = useAuth();
  const token = session!.token;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [updatingTaskId, setUpdatingTaskId] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState<string | null>(null);

  async function loadTasks() {
    setLoadState("loading");
    setLoadError(null);
    try {
      setTasks(await fetchTasks(token));
      setLoadState("success");
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not load tasks.");
      setLoadState("error");
    }
  }

  useEffect(() => {
    loadTasks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleStatusChange(taskId: string, status: TaskStatus) {
    setUpdateError(null);
    setUpdatingTaskId(taskId);
    try {
      const updated = await updateTaskStatus(token, taskId, status);
      setTasks((current) => current.map((task) => (task.id === updated.id ? updated : task)));
    } catch (err) {
      setUpdateError(err instanceof ApiError ? err.message : "Could not update task status.");
    } finally {
      setUpdatingTaskId(null);
    }
  }

  if (loadState === "loading") {
    return <p className="status-text">Loading your tasks...</p>;
  }

  if (loadState === "error") {
    return <p className="error-text">{loadError}</p>;
  }

  const filteredTasks = filterTasksByStatus(tasks, statusFilter);
  const completionPercentage = calculateCompletionPercentage(tasks);

  return (
    <div className="view">
      <section className="card">
        <div className="view-header">
          <h2>My tasks</h2>
          <span className="completion-badge">Completion: {completionPercentage}%</span>
        </div>
        <StatusFilter value={statusFilter} onChange={setStatusFilter} />

        {updateError && <p className="error-text">{updateError}</p>}

        {filteredTasks.length === 0 ? (
          <p className="status-text">No tasks match this filter.</p>
        ) : (
          <table className="task-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Update status</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => (
                <tr key={task.id}>
                  <td>{task.title}</td>
                  <td>{task.status}</td>
                  <td>
                    <select
                      value={task.status}
                      disabled={updatingTaskId === task.id}
                      onChange={(e) => handleStatusChange(task.id, e.target.value as TaskStatus)}
                    >
                      {STATUS_OPTIONS.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
