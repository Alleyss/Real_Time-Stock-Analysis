// src/pages/StockDetailPage.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import toast from 'react-hot-toast';
import Skeleton, { SkeletonTheme } from 'react-loading-skeleton'; // <<< IMPORT SKELETON

// Import Services
import { getStockInfo, getSentimentAnalysis } from '../services/stockService';
import { addToWishlist, removeFromWishlist, checkWishlistItem } from '../services/wishlistService';

// Import Types (adjust paths if needed)
import type { StockInfo, SentimentAnalysisResult, AnalyzedItem } from '../types/stock';
import { SentimentDataSource } from '../types/common'; // Make sure this Enum is defined and imported

// Import Common Components
import Button from '../components/common/Button';
import LoadingSpinner from '../components/common/LoadingSpinner'; // Kept in case needed elsewhere, but skeletons replace some uses
import { formatLargeNumber, formatCurrency } from '../utils/formatters'; // <<< IMPORT FORMATTERS

const StockDetailPage: React.FC = () => {
    // Get ticker from URL parameters
    const { ticker } = useParams<{ ticker: string }>();
    const upperTicker = ticker?.toUpperCase() || 'N/A'; // Ensure uppercase and handle undefined

    // --- State Variables ---
    const [stockInfo, setStockInfo] = useState<StockInfo | null>(null);
    const [sentimentResult, setSentimentResult] = useState<SentimentAnalysisResult | null>(null);
    const [isInWishlist, setIsInWishlist] = useState<boolean | null>(null); // null = loading/unknown, true = yes, false = no
    const [infoLoading, setInfoLoading] = useState<boolean>(true);
    const [sentimentLoading, setSentimentLoading] = useState<boolean>(false);
    const [wishlistCheckLoading, setWishlistCheckLoading] = useState<boolean>(true); // Start true for initial check
    const [isWishlistUpdating, setIsWishlistUpdating] = useState<boolean>(false); // Loading for add/remove action
    const [error, setError] = useState<string | null>(null); // General error display area state

    // --- Data Fetching Callbacks (Memoized) ---
    const fetchInfo = useCallback(async () => {
        if (!ticker) return;
        setInfoLoading(true);
        setError(null); // Clear previous errors
        try {
            const info = await getStockInfo(ticker);
            setStockInfo(info);
            // If the service returns an error structure, display it
            if(info?.error) {
                 setError(`Stock Info Error: ${info.error}`);
                 // Optionally show toast, but might be redundant if displayed below title
                 // toast.error(`Stock Info Error: ${info.error}`);
            }
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Failed to load stock info.';
            setError(errorMsg);
            toast.error(errorMsg);
            console.error("Fetch Info Error:", err);
        } finally {
            setInfoLoading(false);
        }
    }, [ticker]); // Dependency: ticker

    const fetchSentiment = useCallback(async (source: SentimentDataSource) => {
        if (!ticker || sentimentLoading) return; // Prevent concurrent fetches
        setSentimentLoading(true);
        setError(null); // Clear general errors
        setSentimentResult(null); // Clear previous results before new fetch
        try {
            const result = await getSentimentAnalysis(ticker, source);
            setSentimentResult(result);
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : `Failed to load ${source} sentiment.`;
            setError(errorMsg); // Set local error state
            toast.error(errorMsg); // Show toast error
            console.error(`Fetch ${source} Sentiment Error:`, err);
        } finally {
            setSentimentLoading(false);
        }
    }, [ticker, sentimentLoading]); // Dependencies: ticker, sentimentLoading

    const checkWishlistStatus = useCallback(async () => {
        if (!ticker) return;
        setWishlistCheckLoading(true);
        try {
            const item = await checkWishlistItem(ticker);
            setIsInWishlist(!!item); // True if item is not null, false otherwise
        } catch (err) {
            console.error("Error checking wishlist status:", err);
            // Don't set isInWishlist to null here, handle button state based on wishlistCheckLoading
            setIsInWishlist(false); // Default to false if check fails? Or keep null? Let's default to false for button enablement.
            // toast.error("Could not check wishlist status."); // Optional feedback
        } finally {
            setWishlistCheckLoading(false);
        }
    }, [ticker]); // Dependency: ticker

    // --- Effects ---
    useEffect(() => {
        // Fetch initial data when the component mounts or the ticker changes
        fetchInfo();
        checkWishlistStatus();
        setSentimentResult(null); // Reset sentiment on ticker change
        setError(null); // Reset errors on ticker change
    }, [fetchInfo, checkWishlistStatus]); // Depend only on the stable callback functions

    // --- Event Handlers ---
    const handleWishlistToggle = async () => {
        // Prevent action if ticker is missing, already updating, or initial status is unknown (covered by wishlistCheckLoading)
        if (!ticker || isWishlistUpdating || wishlistCheckLoading) return;

        const previousState = isInWishlist ?? false; // Use false if status is null
        setIsInWishlist(!previousState); // Optimistic UI update
        setIsWishlistUpdating(true);

        const actionPromise = previousState
            ? removeFromWishlist(ticker)
            : addToWishlist(ticker);

        toast.promise(
            actionPromise,
            {
                loading: previousState ? 'Removing...' : 'Adding...',
                success: (data) => {
                    setIsWishlistUpdating(false);
                    // Confirm final state matches optimistic state
                    setIsInWishlist(!previousState);
                    return `${data.ticker_symbol} ${previousState ? 'removed from' : 'added to'} wishlist!`;
                },
                error: (err) => {
                    console.error("Wishlist Toggle Error:", err);
                    setIsWishlistUpdating(false);
                    setIsInWishlist(previousState); // Revert optimistic UI
                    return err instanceof Error ? err.message : 'Failed to update wishlist.';
                }
            },
            { /* Optional toast styles */ }
        );
    };

    // --- Rendering Helper ---
    const renderAnalyzedItem = (item: AnalyzedItem, index: number) => {
        const emoji = item.label === 'positive' ? '🟢' : item.label === 'negative' ? '🔴' : '⚪️';
        const key = item.url || item.headline || `item-${index}`;
        return (
            <li key={key} className="py-2 border-b border-gray-200 dark:border-gray-700 last:border-b-0">
                <a href={item.url || '#'} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-600 dark:text-blue-400 text-sm font-medium">
                    {emoji} {item.headline || 'No Headline Available'}
                </a>
                <span className="text-xs text-gray-500 dark:text-gray-400 block mt-1">
                    Source: {item.source_name || 'N/A'} | Score: {item.score?.toFixed(2) ?? 'N/A'}
                </span>
            </li>
        );
    };

    // --- Main Render ---
    return (
        // Configure SkeletonTheme - adjust colors for dark mode if needed
        // Example: baseColor={isDarkMode ? "#374151" : "#e0e0e0"} highlightColor={isDarkMode ? "#4b5563" : "#f5f5f5"}
        // You'd need a way to detect dark mode (e.g., from context or OS preference)
        <SkeletonTheme baseColor="#eee" highlightColor="#f5f5f5">
            <div>
                <h1 className="text-2xl md:text-3xl font-semibold mb-2 flex items-center flex-wrap">
                    {/* Title loading state using Skeleton */}
                    {infoLoading ? <Skeleton width={200} height={30} className="mr-3" /> : <span>{stockInfo?.company_name || 'Stock Details'}</span>}
                    <span className="ml-3 text-blue-600 dark:text-blue-400">{upperTicker}</span>
                </h1>
                 {/* General Error Display */}
                 {error && !infoLoading && !sentimentLoading && (
                     <p className="text-red-500 text-center text-sm mb-4 p-2 bg-red-100 dark:bg-red-900/50 rounded border border-red-300 dark:border-red-700">{error}</p>
                 )}

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* --- Column 1: Stock Info & Wishlist --- */}
                    <div className="md:col-span-1 bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-md self-start">
                        <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100 border-b pb-2 border-gray-200 dark:border-gray-700">Stock Info</h2>
                        {infoLoading ? (
                            // Skeleton Loader for Stock Info Section
                            <div className="space-y-3 text-sm">
                                <p><strong>Company:</strong> <Skeleton width="70%" /></p>
                                <p><strong>Price:</strong> <Skeleton width="40%" /></p>
                                <p><strong>Sector:</strong> <Skeleton width="50%" /></p>
                                <p><strong>Industry:</strong> <Skeleton width="60%" /></p>
                                <p><strong>Market Cap:</strong> <Skeleton width="45%" /></p>
                            </div>
                        ) : stockInfo && !stockInfo.error ? (
                            // Actual Stock Info with Data Formatting
                            <div className="space-y-2 text-sm">
                                <p><strong>Company:</strong> {stockInfo.company_name}</p>
                                <p><strong>Price:</strong> {formatCurrency(typeof stockInfo.current_price === 'number' ? stockInfo.current_price : undefined, stockInfo.currency)}</p>
                                <p><strong>Sector:</strong> {stockInfo.sector || 'N/A'}</p>
                                <p><strong>Industry:</strong> {stockInfo.industry || 'N/A'}</p>
                                <p><strong>Market Cap:</strong> {formatLargeNumber(stockInfo.market_cap)}</p>
                            </div>
                        ) : (
                            // Display error if stock info failed to load
                            <p className="text-gray-500 dark:text-gray-400 py-4 text-center">
                               {stockInfo?.error || "Could not load stock information."}
                            </p>
                        )}
                        {/* Wishlist Button Area */}
                        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
                             {/* Show Skeleton for button only while initially checking wishlist status */}
                             {wishlistCheckLoading ? (
                                 <Skeleton height={40} />
                             ) : (
                                // Show button once initial check is done
                                // Only enable if stock info loaded successfully
                                <Button
                                    onClick={handleWishlistToggle}
                                    isLoading={isWishlistUpdating} // Show spinner only during add/remove action
                                    // Disable if info failed, OR if actively updating
                                    disabled={infoLoading || !!stockInfo?.error || isWishlistUpdating}
                                    variant={isInWishlist ? 'secondary' : 'primary'}
                                    className="w-full"
                                >
                                    {isWishlistUpdating ? (isInWishlist ? 'Adding...' : 'Removing...') : // Text shows action in progress (inverted state due to optim UI)
                                     isInWishlist ? 'Remove from Wishlist' :
                                     'Add to Wishlist'}
                                </Button>
                             )}
                        </div>
                    </div>

                    {/* --- Column 2: Sentiment Analysis --- */}
                    <div className="md:col-span-2 bg-white dark:bg-gray-800 p-4 sm:p-6 rounded-lg shadow-md">
                        <h2 className="text-xl font-semibold mb-4 text-gray-800 dark:text-gray-100 border-b pb-2 border-gray-200 dark:border-gray-700">Sentiment Analysis</h2>
                        {/* Analyze buttons - enable only if stock info loaded */}
                        {stockInfo && !stockInfo.error ? (
                            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4 mb-6">
                                <Button
                                   onClick={() => fetchSentiment(SentimentDataSource.NEWS)}
                                   isLoading={sentimentLoading && sentimentResult?.data_source !== SentimentDataSource.NEWS.valueOf()} // Indicate loading specific source
                                   disabled={sentimentLoading || infoLoading} // Disable both buttons if any analysis is loading or info failed
                                   className="flex-1"
                                >
                                    Analyze News 📰
                                </Button>
                                 <Button
                                   onClick={() => fetchSentiment(SentimentDataSource.REDDIT)}
                                   isLoading={sentimentLoading && sentimentResult?.data_source !== SentimentDataSource.REDDIT.valueOf()}
                                   disabled={sentimentLoading || infoLoading}
                                   className="flex-1"
                                >
                                    Analyze Reddit 👽
                                </Button>
                            </div>
                         ) : (
                            <p className="text-sm text-center text-gray-500 dark:text-gray-400 mb-6">Load stock info first to enable analysis.</p>
                         )}

                        {/* Sentiment Results Display Area */}
                        {sentimentLoading ? (
                             // Skeleton Loader for Sentiment Results Section
                             <div className="space-y-6">
                                 {/* Summary Skeleton */}
                                 <div className="p-4 rounded bg-gray-100/50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600/50">
                                    <h3 className="font-semibold text-lg mb-3"><Skeleton width="60%" /></h3>
                                    <div className="space-y-2 text-sm">
                                        <div className="flex justify-between items-center"><Skeleton width="40%" /> <Skeleton width="20%" /></div>
                                        <div className="flex justify-between items-center"><Skeleton width="30%" /> <Skeleton width="25%" /></div>
                                    </div>
                                    <p className="text-xs mt-3"><Skeleton width="50%" /></p>
                                </div>
                                {/* Justification Skeleton */}
                                <div>
                                     <h4 className="font-medium mb-2"><Skeleton width="45%" /></h4>
                                     <ul className="space-y-2 text-xs list-disc list-inside pl-2"><Skeleton count={2} /></ul>
                                </div>
                                {/* Analyzed Items Skeleton */}
                                <div>
                                     <h4 className="font-medium mb-2"><Skeleton width="55%" /></h4>
                                     <ul className="space-y-3 border rounded p-2 bg-gray-50/50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700/50">
                                         <Skeleton count={5} height={35} /> {/* Simulate list items */}
                                     </ul>
                                </div>
                            </div>
                        ) : sentimentResult ? (
                            // Actual Sentiment Results (structure same as before)
                            <div className="space-y-5">
                               {/* Summary Section */}
                               <div className="p-4 rounded bg-gray-100 dark:bg-gray-700 border border-gray-200 dark:border-gray-600 shadow-sm">
                                    <h3 className="font-semibold text-lg mb-2">Analysis Summary ({sentimentResult.data_source})</h3>
                                    <div className="flex justify-between items-center text-sm mb-1">
                                        <span>Aggregated Score:</span>
                                        <span className={`font-bold text-lg ${sentimentResult.aggregated_score > 0.05 ? 'text-green-600 dark:text-green-400' : sentimentResult.aggregated_score < -0.05 ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'}`}>
                                            {sentimentResult.aggregated_score.toFixed(3)}
                                        </span>
                                    </div>
                                    <div className="flex justify-between items-center text-sm">
                                        <span id='suggestion'>Suggestion:</span>
                                        <span id='suggestion1'className="font-bold text-base">{sentimentResult.suggestion}</span>
                                    </div>
                                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Based on {sentimentResult.analyzed_articles_count} analyzed items.</p>
                               </div>

                               {/* Justification Points */}
                               {sentimentResult.justification_points?.length > 0 && (
                                   <div>
                                       <h4 className="font-medium mb-2 text-gray-700 dark:text-gray-300">Justification Points:</h4>
                                       <ul className="space-y-2 text-xs list-disc list-inside pl-2">
                                            {sentimentResult.justification_points.map((point, index) => {
                                                const emoji = point.type === 'positive' ? '🟢' : point.type === 'negative' ? '🔴' : '⚪️';
                                                return (
                                                    <li key={index}>
                                                        {emoji} <a href={point.url || '#'} target="_blank" rel="noopener noreferrer" className="hover:underline text-blue-600 dark:text-blue-400">{point.headline || 'N/A'}</a> <span className="text-gray-600 dark:text-gray-400">({point.source || 'N/A'}, Score: {point.score?.toFixed(2) ?? 'N/A'})</span>
                                                    </li>
                                                );
                                            })}
                                       </ul>
                                   </div>
                               )}

                               {/* Top Analyzed Items List */}
                               {sentimentResult.top_analyzed_items?.length > 0 && (
                                   <div>
                                       <h4 className="font-medium mb-2 text-gray-700 dark:text-gray-300">Top Analyzed Items:</h4>
                                       <ul className="space-y-1 max-h-96 overflow-y-auto pr-2 border rounded p-2 bg-gray-50 dark:bg-gray-900/30 border-gray-200 dark:border-gray-700">
                                           {sentimentResult.top_analyzed_items.map(renderAnalyzedItem)}
                                       </ul>
                                   </div>
                               )}
                            </div>
                        ) : (
                            // Initial state or state after clearing results
                            <p className="text-center text-gray-500 dark:text-gray-400 py-8 italic">
                                {stockInfo && !stockInfo.error
                                    ? "Select a source (News or Reddit) to perform sentiment analysis."
                                    : "Analysis unavailable until stock info is loaded."}
                            </p>
                        )}
                    </div>
                </div>
            </div>
         </SkeletonTheme>
    );
};

export default StockDetailPage;