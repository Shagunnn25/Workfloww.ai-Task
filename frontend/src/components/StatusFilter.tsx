import type { TaskStatus } from "../types/task";

interface StatusFilterProps {
  value: TaskStatus | "all";
  onChange: (value: TaskStatus | "all") => void;
}

export function StatusFilter({ value, onChange }: StatusFilterProps) {
  return (
    <label className="status-filter">
      Filter by status:
      <select value={value} onChange={(e) => onChange(e.target.value as TaskStatus | "all")}>
        <option value="all">All</option>
        <option value="pending">Pending</option>
        <option value="in_progress">In progress</option>
        <option value="completed">Completed</option>
      </select>
    </label>
  );
}
