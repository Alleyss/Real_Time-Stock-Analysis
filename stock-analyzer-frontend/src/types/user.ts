// src/types/user.ts
export interface UserBase {
    email: string;
    username?: string | null; // Optional, matches Pydantic
  }
  
  export interface UserCreate extends UserBase {
    password: string;
  }
  
  export interface User extends UserBase {
    id: number;
    is_active: boolean;
    created_at: string; // Keep as string from API, can parse to Date object if needed
  }