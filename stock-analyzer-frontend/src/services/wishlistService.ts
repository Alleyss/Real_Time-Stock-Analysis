// src/services/wishlistService.ts
import apiClient from './api';
import type { WishlistItem, WishlistItemCreate } from '../types/wishlist'; // Adjust path as needed

// Fetch user's wishlist
export const getWishlist = async (): Promise<WishlistItem[]> => {
    try {
        // Assuming the backend returns List[WishlistItem] directly
        const response = await apiClient.get<WishlistItem[]>('/wishlist/');
        return response.data;
    } catch (error: any) {
        console.error('Error fetching wishlist:', error);
        // Handle error appropriately, maybe return empty array or throw
        return [];
    }
};

// Add item to wishlist
export const addToWishlist = async (tickerSymbol: string): Promise<WishlistItem> => {
    try {
        const payload: WishlistItemCreate = { ticker_symbol: tickerSymbol };
        const response = await apiClient.post<WishlistItem>('/wishlist/', payload);
        return response.data;
    } catch (error: any) {
        console.error(`Error adding ${tickerSymbol} to wishlist:`, error);
        const detail = error.response?.data?.detail || `Failed to add ${tickerSymbol}`;
        throw new Error(detail); // Rethrow for component to handle
    }
};

// Remove item from wishlist
export const removeFromWishlist = async (tickerSymbol: string): Promise<WishlistItem> => {
     // Backend returns the deleted item
    try {
        const upperTicker = tickerSymbol.toUpperCase();
        const response = await apiClient.delete<WishlistItem>(`/wishlist/${upperTicker}`);
        return response.data;
    } catch (error: any) {
        console.error(`Error removing ${tickerSymbol} from wishlist:`, error);
         const detail = error.response?.data?.detail || `Failed to remove ${tickerSymbol}`;
        throw new Error(detail); // Rethrow for component to handle
    }
};

// Optional: Check if item is in wishlist (backend endpoint might not exist - could infer from getWishlist)
export const checkWishlistItem = async (tickerSymbol: string): Promise<WishlistItem | null> => {
     try {
        const upperTicker = tickerSymbol.toUpperCase();
        const response = await apiClient.get<WishlistItem>(`/wishlist/${upperTicker}`);
        return response.data; // Returns item if found
    } catch (error: any) {
         if (error.response && error.response.status === 404) {
             return null; // 404 means not found, which is valid info here
         }
         console.error(`Error checking wishlist for ${tickerSymbol}:`, error);
         return null; // Return null on other errors too? Or throw?
     }
};