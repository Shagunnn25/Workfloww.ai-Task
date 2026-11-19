export type UserRole = "manager" | "employee";

export interface User {
  full_name: string;
  role: UserRole;
}

export interface Employee {
  id: string;
  full_name: string;
  email: string;
}

export interface Company {
  id: string;
  name: string;
}
