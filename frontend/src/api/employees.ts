import type { Employee } from "../types/user";
import { apiRequest } from "./client";

export async function fetchEmployees(token: string): Promise<Employee[]> {
  return apiRequest<Employee[]>("/employees", { token });
}
