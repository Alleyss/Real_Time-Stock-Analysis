// src/types/wishlist.ts (Example)

export interface WishlistItemCreate {
  ticker_symbol: string;
}

export interface WishlistItem {
  id: number;
  ticker_symbol: string;
  user_id: number; // May not need this often on frontend, but good for typing
  added_at: string; // Or Date
}