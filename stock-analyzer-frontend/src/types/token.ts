// src/types/token.ts
export interface Token { // <<< Make sure 'export interface Token' is exactly like this
    access_token: string;
    token_type: string;
  }
  
  // This is also used by your backend deps.py if you have TokenData for JWT decoding
  // If not used by authService.ts directly yet, it's fine for it to be here.
  export interface TokenData {
    identifier?: string | null; // Stores the 'sub' from JWT (e.g., user's email)
  }