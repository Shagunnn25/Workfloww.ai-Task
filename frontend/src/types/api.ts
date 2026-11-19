import type { UserRole } from "./user";

export interface ApiErrorResponse {
  error: string;
  message: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  role: UserRole;
  full_name: string;
}
