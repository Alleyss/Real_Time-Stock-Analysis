// src/pages/WishlistPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import { FiTrash2, FiExternalLink, FiLoader } from 'react-icons/fi'; // Icons

// Services and Types
import { getWishlist, removeFromWishlist } from '../services/wishlistService';
import type { WishlistItem } from '../types/wishlist';

// Common Components
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner'; // For main loading state

const WishlistPage: React.FC = () => {
    const [wishlist, setWishlist] = useState<WishlistItem[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [error, setError] = useState<string | null>(null);
    // State to track which item is currently being removed (for button loading state)
    const [removingTicker, setRemovingTicker] = useState<string | null>(null);

    // Fetch wishlist data on component mount
    const fetchWishlistData = useCallback(async () => {
        setIsLoading(true);
        setError(null);
        try {
            const data = await getWishlist();
            setWishlist(data);
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to fetch wishlist';
            setError(errorMsg);
            toast.error(errorMsg); // Show toast on fetch error
            console.error("Fetch Wishlist Error:", err);
        } finally {
            setIsLoading(false);
        }
    }, []); // Empty dependency array means run once on mount

    useEffect(() => {
        fetchWishlistData();
    }, [fetchWishlistData]);

    // Handle removing an item
    const handleRemove = async (ticker: string) => {
        if (removingTicker) return; // Prevent multiple removals at once

        setRemovingTicker(ticker); // Set loading state for this specific button

        const actionPromise = removeFromWishlist(ticker);

        toast.promise(
            actionPromise,
            {
                loading: `Removing ${ticker}...`,
                success: (removedItem) => {
                    // Update local state by filtering out the removed item
                    setWishlist(currentList => currentList.filter(item => item.ticker_symbol !== removedItem.ticker_symbol));
                    setRemovingTicker(null); // Clear loading state
                    return `${removedItem.ticker_symbol} removed from wishlist!`;
                },
                error: (err) => {
                    setRemovingTicker(null); // Clear loading state
                    return err instanceof Error ? err.message : `Failed to remove ${ticker}.`;
                }
            },
             { // Optional: Customize toast appearance
                style: { minWidth: '250px' },
                success: { duration: 3000 },
                error: { duration: 4000 }
            }
        );
    };

    // --- Render Logic ---

    // Main loading state for the whole page
    if (isLoading) {
        return (
            <div className="flex justify-center items-center py-20">
                <LoadingSpinner text="Loading your wishlist..." />
            </div>
        );
    }

    // Error state after loading
    if (error && wishlist.length === 0) { // Show error prominently if list couldn't be loaded
        return (
            <div className="text-center py-10">
                <p className="text-red-500 dark:text-red-400">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchWishlistData} className="mt-4">
                    Retry
                </Button>
            </div>
        );
    }

    return (
        <div className="animate-slide-in max-w-4xl mx-auto"> {/* Center content */}
            <h1 className="text-3xl font-bold mb-6 border-b border-[var(--border-color)] pb-3 text-[var(--text-primary)]">
                My Watchlist
            </h1>

            {/* Show retry button even if list is partially loaded but error occurred */}
             {error && (
                 <div className="mb-4 text-center">
                     <p className="text-red-500 dark:text-red-400 text-sm">{error}</p>
                     <Button variant="outline" size="sm" onClick={fetchWishlistData} className="mt-2">
                        Retry Fetch
                     </Button>
                 </div>
             )}

            {wishlist.length === 0 ? (
                <div className="text-center py-10 bg-[var(--bg-secondary)] rounded-lg shadow">
                    <FiHeart className="mx-auto text-4xl text-[var(--text-muted)] mb-3"/>
                    <p className="text-[var(--text-secondary)]">Your wishlist is empty.</p>
                    <p className="text-sm text-[var(--text-muted)] mt-1">Search for stocks and add them!</p>
                    <Link to="/dashboard"> {/* Link back to dashboard/search */}
                         <Button variant="primary" size="sm" className="mt-4">
                             Find Stocks
                         </Button>
                    </Link>
                </div>
            ) : (
                <div className="bg-[var(--bg-primary)] border border-[var(--border-color)] rounded-lg shadow-md overflow-hidden">
                    <ul className="divide-y divide-[var(--border-color)]">
                        {wishlist.map((item) => {
                            const isRemoving = removingTicker === item.ticker_symbol;
                            return (
                                <li
                                    key={item.id}
                                    className="flex flex-col sm:flex-row justify-between items-center p-4 sm:p-5 hover:bg-[var(--bg-tertiary)] transition-colors duration-150 ease-in-out"
                                >
                                    <Link
                                        to={`/stock/${item.ticker_symbol}`}
                                        className="font-semibold text-lg text-[var(--accent-secondary)] hover:text-[var(--accent-primary)] hover:underline mb-2 sm:mb-0"
                                    >
                                        {item.ticker_symbol}
                                    </Link>
                                    <div className="flex space-x-3">
                                        <Link to={`/stock/${item.ticker_symbol}`}>
                                            <Button
                                                variant="outline"
                                                size="sm"
                                                className="w-auto"
                                                title={`View ${item.ticker_symbol} details`}
                                                leftIcon={<FiExternalLink size={14}/>}
                                            >
                                               View
                                            </Button>
                                        </Link>
                                        <Button
                                            variant="danger"
                                            size="sm"
                                            className="w-auto"
                                            onClick={() => handleRemove(item.ticker_symbol)}
                                            isLoading={isRemoving} // Show loading on the specific button
                                            disabled={!!removingTicker} // Disable all remove buttons if one is working
                                            leftIcon={<FiTrash2 size={14}/>}
                                        >
                                            {isRemoving ? 'Removing...' : 'Remove'}
                                        </Button>
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default WishlistPage;