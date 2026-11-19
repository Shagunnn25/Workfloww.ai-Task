import { useEffect, useState, type FormEvent } from "react";
import { fetchEmployees } from "../api/employees";
import { ApiError } from "../api/client";
import { createTask, fetchTasks } from "../api/tasks";
import { useAuth } from "../context/AuthContext";
import type { Task, TaskStatus } from "../types/task";
import type { Employee } from "../types/user";
import { filterTasksByStatus } from "../utils/taskFilters";
import { calculateCompletionPercentage } from "../utils/taskStats";
import { StatusFilter } from "./StatusFilter";

type LoadState = "loading" | "success" | "error";

export function ManagerView() {
  const { session } = useAuth();
  const token = session!.token;

  const [tasks, setTasks] = useState<Task[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [loadState, setLoadState] = useState<LoadState>("loading");
  const [loadError, setLoadError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  async function loadData() {
    setLoadState("loading");
    setLoadError(null);
    try {
      const [taskList, employeeList] = await Promise.all([fetchTasks(token), fetchEmployees(token)]);
      setTasks(taskList);
      setEmployees(employeeList);
      setLoadState("success");
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : "Could not load tasks.");
      setLoadState("error");
    }
  }

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreateTask(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    setIsCreating(true);
    try {
      await createTask(token, {
        title,
        description: description || undefined,
        assigned_to: assignedTo,
        due_date: dueDate || undefined,
      });
      setTitle("");
      setDescription("");
      setAssignedTo("");
      setDueDate("");
      await loadData();
    } catch (err) {
      setFormError(err instanceof ApiError ? err.message : "Could not create task.");
    } finally {
      setIsCreating(false);
    }
  }

  if (loadState === "loading") {
    return <p className="status-text">Loading tasks...</p>;
  }

  if (loadState === "error") {
    return <p className="error-text">{loadError}</p>;
  }

  const filteredTasks = filterTasksByStatus(tasks, statusFilter);
  const completionPercentage = calculateCompletionPercentage(tasks);

  return (
    <div className="view">
      <section className="card">
        <h2>Create task</h2>
        <form onSubmit={handleCreateTask} className="task-form">
          <label htmlFor="title">Title</label>
          <input id="title" value={title} onChange={(e) => setTitle(e.target.value)} required />

          <label htmlFor="description">Description</label>
          <textarea id="description" value={description} onChange={(e) => setDescription(e.target.value)} />

          <label htmlFor="assignedTo">Assign to</label>
          <select id="assignedTo" value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)} required>
            <option value="" disabled>
              Select an employee
            </option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id}>
                {employee.full_name}
              </option>
            ))}
          </select>

          <label htmlFor="dueDate">Due date</label>
          <input id="dueDate" type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />

          {formError && <p className="error-text">{formError}</p>}

          <button type="submit" disabled={isCreating}>
            {isCreating ? "Creating..." : "Create task"}
          </button>
        </form>
      </section>

      <section className="card">
        <div className="view-header">
          <h2>Company tasks</h2>
          <span className="completion-badge">Completion: {completionPercentage}%</span>
        </div>
        <StatusFilter value={statusFilter} onChange={setStatusFilter} />

        {filteredTasks.length === 0 ? (
          <p className="status-text">No tasks match this filter.</p>
        ) : (
          <table className="task-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Assignee</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => (
                <tr key={task.id}>
                  <td>{task.title}</td>
                  <td>{task.assignee_name}</td>
                  <td>{task.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
