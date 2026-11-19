export type TaskStatus = "pending" | "in_progress" | "completed";

export interface Task {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  assigned_to: string;
  assignee_name: string;
  created_by: string;
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaskCreateInput {
  title: string;
  description?: string;
  assigned_to: string;
  due_date?: string;
}
