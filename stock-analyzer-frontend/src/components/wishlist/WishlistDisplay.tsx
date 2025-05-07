// src/components/wishlist/WishlistDisplay.tsx
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getWishlist, removeFromWishlist } from '../../services/wishlistService';
import type { WishlistItem } from '../../types/wishlist';
import Button from '../common/Button'; // Assuming you have a Button component

const WishlistDisplay: React.FC = () => {
  const [wishlist, setWishlist] = useState<WishlistItem[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchWishlistData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getWishlist();
      setWishlist(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch wishlist');
      console.error("Fetch Wishlist Error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchWishlistData();
  }, []); // Fetch on component mount

  const handleRemove = async (ticker: string) => {
      // Optional: Add confirmation dialog
      try {
          await removeFromWishlist(ticker);
          // Refresh list after removal
          setWishlist(currentList => currentList.filter(item => item.ticker_symbol !== ticker));
          // Or call fetchWishlistData(); again, but filtering is more efficient
      } catch (err) {
          setError(err instanceof Error ? err.message : `Failed to remove ${ticker}`);
          console.error(`Remove Wishlist Error (${ticker}):`, err);
          // Optionally show error to user via toast/notification
      }
  };


  if (isLoading) {
    return <div className="text-center p-4">Loading wishlist...</div>;
  }

  return (
    <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-md mt-8">
      <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-100">My Wishlist</h2>
       {error && <p className="text-red-500 text-sm mb-4 text-center">{error}</p>}
      {wishlist.length === 0 ? (
        <p className="text-gray-600 dark:text-gray-400">Your wishlist is empty. Search for stocks to add them.</p>
      ) : (
        <ul className="space-y-3">
          {wishlist.map((item) => (
            <li
              key={item.id}
              className="flex justify-between items-center p-3 bg-gray-50 dark:bg-gray-700 rounded hover:bg-gray-100 dark:hover:bg-gray-600 transition duration-150 ease-in-out"
            >
              <Link
                to={`/stock/${item.ticker_symbol}`}
                className="font-medium text-blue-600 dark:text-blue-400 hover:underline"
              >
                {item.ticker_symbol}
              </Link>
              <Button
                 variant="danger"
                 className="w-auto px-3 py-1 text-xs" // Smaller button
                 onClick={() => handleRemove(item.ticker_symbol)}
                 // Optional: Add loading state per button if removal is slow
              >
                Remove
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default WishlistDisplay;